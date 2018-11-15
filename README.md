# Logstash pipeline integration testing

Make integration testing of Logstash configuration easily usable for sysadmins.

When using the [Elastic Stack for Log
Management](https://www.elastic.co/solutions/logging) you will topically use
[Logstash](https://www.elastic.co/products/logstash) for log processing and transformation.
In Logstash, you can configure the processing pieplines using configuration files.
Such configuration can get complex, things like grok patterns and multiple
inputs make it difficult to make changes and enhancements confidently
without breaking anything.

When we started using Logstash @geberit, there was the need for
an easy to use integration testing environment for quality assurance reasons.
At the time, nothing publicly available suited our needs so we created our own.

Most of the heavy lifting is done for you in this environment so you can
concentrate on writing your Logstash configuration.

## Design principles

* Make Logstash output pretty (JSON) and deterministic.

  Things like `@timestamp` and `host` are set by Logstash if not yet present in the
	event. This would make tests non-deterministic thus such fields are set to
	static values by the test environment.

* Avoid overhead and allow flexibility.

  Defining each log line in a unit test did not suit us because it
  is high maintenance when things are changed as you would need to run the
  tests, copy in the new outputs and then run the tests again to see them
  passing. The copy part and subsequent run of the tests has been avoided.

* Use git for checking if tests passed.

  The Logstash output files are checked into git along with the Logstash configuration and input files.
  Together with the advantages of tracking configuration with git, including the
  input and output makes it very transparent what a change in input or config
  has on the output. This can all be tracked in one commit.

* Selective testing and bulk testing.

  Selective testing is more what you are (hopefully) used to from unit testing, you try to think about all the possibilities and write a test for each of them to see how the thing you are testing behaves. This is great for writing the configuration but once it is there, you might additionally want to throw some bulkier test data at it.

* Isolated.

	You can set this environment up on one of your Logstash hosts or preferably a
	separate test system. Either way, the test environment is self contained and
	isolated.

* Written by sysadmins for sysadmins.

	The main script is in Bash which any sysadmin should be familiar with. Bash
	was chosen because the main script `run_tests` interacts with other
	CLI programs for the most part. Python is used when it comes to JSON parsing and searching for errors.

## Requirements

* GNU/Linux host
* Installed and basic knowledge: bash, git, make, rsync, jq, python3, ${EDITOR:-vim}
* Logstash installed, v5.5.0 and above are recommended and used with this test environment
  The test environment is currently only known to work with it's full feature set with Logstash v5.5.0.
	Issue `rm conf.d/2_filter_remove_comment_lines.conf` in your test env if you are using 6.0+ for now.

## Setup

```Shell
git init logstash-test-env
cd logstash-test-env
git submodule add https://github.com/geberit/logstash-config-integration-testing.git logstash-config-integration-testing
cd logstash-config-integration-testing
make setup
cd ..
```

## Quick start: Example for adding a test

```Shell
rsync -r logstash-config-integration-testing/examples/zypper-eventlog/ .
make run-tests
git add .
git commit
```

Now you can make changes as you like and see the result using git.

## Usage in detail

Run `make run-tests`. It will ask you to start
a Logstash instance with the specified parameters. You are advised to start
this Logstash instance in a separate shell. After the pipeline has started,
press return (`run-tests`). `run-tests` will now remove the files below
`./output` and pipe the files below `./input/` into Logstash using Unix sockets.
Logstash will then write to `./output`. `./output` is version controlled so you can
check if the output changed using `git diff ./output`. To accept the diff, just
make a git commit.

The git diffing has been further automated and can be run using `make check`.
For normal development it is recommended to run `make run-tests` and the
appropriate git commands directly.

Additional to the `make run-tests` (selective testing) where git
diffing/manual review is used to catch issues there is also
`make run-bulk-tests` where the output is not checked into git and not intended to be manually reviewed.
Instead, `make run-bulk-tests` searches for common errors like translate or grok parse failures.

## Add new input

New input can be added to the appropriate file below `./input/` (selective testing) or `./input_bulk` (bulk testing).
The filename has to match the [#source] field for which the 5_filter logstash config files check for.
Example: `./input/zypper-eventlog.log` automatically gets the field `[#source] == "zypper-eventlog"` attached at Logstash input stage so in the filter stage, `if [#source] == "zypper-eventlog" {` can be used.

The file suffix has a special meaning and the following suffixes are supported:

* `log`: The logfile is expected to contain raw log lines without any serialization like JSON encoding applied. Example log line:

	```
  5,Aug  3 13:16:40,[unset],date=2017-08-03,time=13:16:40,devname=example_host
	```

* `json`: The logfile is expected to contain JSON encoded log lines and should be de-serialized in the Logstash input stage. Example log line:

	```JSON
	{"@timestamp":"2017-08-22T14:26:18.247Z","offset":15805855,"input_type":"log","beat":{"hostname":"gnu.example.org","name":"gnu.example.org","version":"5.3.1"},"host":"gnu.example.org","source":"/var/log/icinga/icinga.log","message":"[1503411978] Warning: The results of service 'http-url-redirected' on host 'www.example.org' are stale by 0d 0h 0m 28s","type":"log","tags":["beats_input_codec_plain_applied"]}
	```

## Deploying to production

The Logstash input and output directives are managed by the test environment. You will need to write those for production manually.
Have a look at the example files below `./ls_etc_deploy_parts/conf.d/` that you can modify and use as a starting point.

Changes should always be done in the test environment, properly tested and committed to git. After that, you can deploy directly from the test environment or setup other means of deployment like CI pipelines.

Install the test-config to real-world Logstash servers:

	./deploy "$hostname"

## Known issues

* `sleep` duration might need to be increased for Logstash to write the events out in time before `./run_tests` does it’s post processing. `./run_tests` will source `./run_tests.conf` if it is present in the current working directory where `sleep_time_for_logstash_flush` can be adjusted.
* Support for [Multiple pipelines in Logstash](https://www.elastic.co/blog/logstash-multiple-pipelines).

## License

[AGPL-3.0-only](https://www.gnu.org/licenses/agpl-3.0.html)

* Author Copyright (C) 2017-2018 Robin Schneider
* Company Copyright (C) 2017-2018 [Geberit Verwaltungs GmbH](https://www.geberit.de)
