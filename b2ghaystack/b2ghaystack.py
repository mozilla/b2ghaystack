# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import logging
import re
import time
import sys

from bs4 import BeautifulSoup
import jenkins
import requests


def url_links(url, regex=None, auth=None):
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    soup = BeautifulSoup(r.text)
    links = [link.get('href') for link in soup.find_all('a')]
    if regex:
        return [link for link in links if re.match(regex, link)]
    else:
        return links


def get_builds(branch, device, good_rev, bad_rev, eng=False, max_builds=10.,
               auth=None):
    revisions = []
    path = '' if branch == 'mozilla-central' else 'integration/'
    pushlog_url = 'https://hg.mozilla.org/%s%s/json-pushes?fromchange=%s' \
        '&tochange=%s' % (path, branch, good_rev, bad_rev)
    print 'Getting revisions from: %s' % pushlog_url
    r = requests.get(pushlog_url)
    r.raise_for_status()

    pushlog = r.json()
    for push_id in sorted(pushlog.keys()):
        push = pushlog[push_id]
        revision = push['changesets'][-1]
        if revision[:12] not in (good_rev[:12], bad_rev[:12]):
            revisions.append((revision, push['date']))
    print '--------> %d revisions found' % len(revisions)

    revisions.sort(key=lambda r: r[1])  # sort revisions by date
    if not revisions:
        return []
    start_time = revisions[0][1]
    end_time = revisions[-1][1]
    raw_revisions = map(lambda l: l[0], revisions)

    base_url = 'https://pvtbuilds.mozilla.org/pvt/mozilla.org/b2gotoro/' \
               'tinderbox-builds/%s-%s%s/' % (
                   branch, device, '-eng' if eng else '')

    range = 60 * 60 * 4  # anything within four hours
    format = '%Y%m%d%H%M%S'
    print 'Getting builds from: %s' % base_url
    ts = map(lambda l: int(time.mktime(time.strptime(l.strip('/'), format))),
             url_links(base_url, '^\d{14}/$', auth))
    print '--------> %d builds found' % len(ts)
    ts_in_range = filter(lambda t: t > (start_time - range) and
                         t < (end_time + range), ts)
    print '--------> %d builds within range' % len(ts_in_range)
    all_builds = []
    for ts in ts_in_range:
        build_url = '%s%s/' % (
            base_url, time.strftime(format, time.localtime(ts)))
        for link in url_links(build_url, '^sources\.xml$', auth):
            sources_url = '%s/%s' % (build_url, link)
            r = requests.get(sources_url, auth=auth)
            search = re.search('<project .* path="gecko" remote="hgmozillaorg"'
                               ' revision="(\w{12})"/>', r.text)
            if search:
                for revision in raw_revisions:
                    if search.group(1) == revision[:12]:
                        all_builds.append({
                            'revision': revision,
                            'timestamp': ts,
                            'url': build_url})
    print '--------> %d builds matching revisions' % len(all_builds)
    if len(all_builds) > max_builds:
        builds = []
        divisor = len(all_builds) / max_builds
        print 'Build count exceeds maximum. Selecting interspersed builds.'
        for i, build in enumerate(all_builds):
            if i % divisor < 1:
                builds.append(build)
    else:
        builds = all_builds
    if len(builds) > 0:
        print '--------> %d builds selected (%s:%s)' % (
            len(builds),
            builds[0]['revision'][:12],
            builds[-1]['revision'][:12])
    return builds


def cli(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Trigger Jenkins jobs for all builds between revisions.')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='verbose output')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='output the jobs to console without triggering them')
    parser.add_argument(
        '-m',
        dest='max_builds',
        type=int,
        default=10.,
        help='maximum number of builds to trigger (default: %(default)s)')
    parser.add_argument(
        '-b',
        dest='branch',
        default='mozilla-central',
        help='branch to use (default: %(default)s)')
    parser.add_argument(
        '--eng',
        action='store_true',
        default=False,
        help='limit to engineering builds')
    parser.add_argument(
        '-a',
        dest='apps',
        metavar='APP',
        nargs='*',
        help='names of applications to test')
    parser.add_argument(
        '-u',
        dest='username',
        help='username for access to the builds')
    parser.add_argument(
        '-p',
        dest='password',
        help='password for access to the builds')
    parser.add_argument(
        '-j',
        dest='jenkins_url',
        default='http://localhost:8080',
        help='url of jenkins instance (default: %(default)s)')
    parser.add_argument(
        '-e',
        dest='email',
        help='email address to send result notifications')
    parser.add_argument(
        'device_name',
        help='name of device')
    parser.add_argument(
        'job_name',
        help='name of the jenkins job to execute')
    parser.add_argument(
        'good_rev',
        help='last known good revision')
    parser.add_argument(
        'bad_rev',
        help='first known bad revision')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARN
    logging.basicConfig(level=log_level)

    auth = any([args.username, args.password]) and \
        (args.username, args.password) or None

    builds = get_builds(args.branch, args.device_name, args.good_rev,
                        args.bad_rev, args.eng, args.max_builds, auth)

    j = jenkins.Jenkins(args.jenkins_url)
    if builds:
        parameters = {'NOTIFICATION_ADDRESS': args.email}
        if args.apps:
            print 'Application%s under test: %s' % (
                's' if len(args.apps) > 1 else '', ', '.join(args.apps))
            parameters.update({'APPS': ','.join(args.apps)})
        print 'Results will be sent to: %s' % args.email
        for build in builds:
            parameters.update({
                'BUILD_REVISION': build['revision'],
                'BUILD_TIMESTAMP': time.strftime(
                    '%d %B %Y %H:%M:%S', time.localtime(build['timestamp'])),
                'BUILD_LOCATION': build['url']})
            print 'Triggering %s for revision: %s (%s)' % (
                args.job_name, build['revision'][:12], build['timestamp'])
            if not args.dry_run:
                j.build_job(args.job_name, parameters)
                time.sleep(0.5)
    else:
        print 'No builds to trigger.'

if __name__ == '__main__':
    cli()
