# b2ghaystack

b2ghaystack is a tool to assist in searching for B2G regressions by triggering
jobs in Jenkins for each build between two revisions.

## Requirements

You must have a [Jenkins](http://jenkins-ci.org/) instance running that you can
reach with at least one job configured with the following parameters:

* BUILD_REVISION - This will be populated with the revision of the build that will be tested.
* BUILD_TIMESTAMP - A formatted timestamp of the selected build for inclusion in the e-mail notification.
* BUILD_LOCATION - The URL of build to download.
* APPS - A comma separated names of the applications to test.
* NOTIFICATION_ADDRESS - The e-mail address to send the results to.

## Installation

With pip and git installed you can use:

    pip install git+git://github.com/davehunt/b2ghaystack.git#egg=b2ghaystack

If you anticipate modifying b2ghaystack, you can instead:

    git clone git://github.com/davehunt/b2ghaystack.git
    cd b2ghaystack
    python setup.py develop

## Usage

```
usage: b2ghaystack [-h] [-v] [--dry-run] [-m MAX_BUILDS] [-b BRANCH] [--eng]
                   [-a [APP [APP ...]]] [-u USERNAME] [-p PASSWORD]
                   [-j JENKINS_URL] [-e EMAIL]
                   device_name job_name good_rev bad_rev

Trigger Jenkins jobs for all builds between revisions.

positional arguments:
  device_name         name of device
  job_name            name of the jenkins job to execute
  good_rev            last known good revision
  bad_rev             first known bad revision

optional arguments:
  -h, --help          show this help message and exit
  -v, --verbose       verbose output
  --dry-run           output the jobs to console without triggering them
  -m MAX_BUILDS       maximum number of builds to trigger (default: 10.0)
  -b BRANCH           branch to use (default: mozilla-central)
  --eng               limit to engineering builds
  -a [APP [APP ...]]  names of applications to test
  -u USERNAME         username for access to the builds
  -p PASSWORD         password for access to the builds
  -j JENKINS_URL      url of jenkins instance (default: http://localhost:8080)
  -e EMAIL            email address to send result notifications
  ```
