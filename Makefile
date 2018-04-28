## vim: foldmarker={{{,}}} foldlevel=0 foldmethod=marker spell:

## This makefile uses :: to define targets so that the targets can be extended.
## https://stackoverflow.com/questions/1644920/override-target-in-makefile-to-add-more-commands/1645332#1645332

## Variables {{{
SHELL := /bin/bash
LOGSTASH_PLUGIN ?= /usr/share/logstash/bin/logstash-plugin
RSYNC_DEPLOY_OPTIONS ?= --copy-links --recursive --verbose --prune-empty-dirs --filter='. logstash-config-integration-testing/rsync_deploy_filter'
## }}}

.PHONY: FORCE_MAKE

.PHONY: default
default: list

## list targets (help) {{{
.PHONY: list
# https://stackoverflow.com/a/26339924/2429985
list:
	@echo "This Makefile has the following targets:"
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^(:?[^[:alnum:]]|FORCE_MAKE$$)' -e '^$@$$' | sed 's/^/    /'
## }}}

# This commands needs to be run from inside of logstash-config-integration-testing/.
.PHONY: setup
setup: project_template/
	mkdir --parents ../input/ ../conf.d/
	cp --recursive --interactive $</.gitignore $</* ../
	ln --relative --symbolic --force ./conf.d/* ../conf.d/

.PHONY: run-tests
run-tests:: ./logstash-config-integration-testing/run_tests
	"$<"

.PHONY: run-bulk-tests
run-bulk-tests:: ./logstash-config-integration-testing/run_tests
	"$<" '.' 'bulk'

.PHONY: check
check:: check-integration-testing

.PHONY: check-integration-testing
check-integration-testing::
	if ! git diff --quiet -- output/; then echo "Please ensure that ./output/ is clean in git." 1>&2; exit 3; fi
	$(MAKE) run-tests
	git diff --quiet -- output/
	# git add output/
	$(MAKE) run-bulk-tests

.PHONY: install-deps
install-deps::
	## `$(LOGSTASH_PLUGIN) install` needs a little bit of encouragement using `yes`.
	yes | $(LOGSTASH_PLUGIN) install logstash-filter-translate

.PHONY: live
live::

.PHONY: install
install: live

.PHONY: push
push: live

.PHONY: prepare-local-restore
prepare-local-restore:: ./deploy
	rm -rf ls_etc_local_restore/conf.d/ ls_etc_local_restore/includes/ ls_etc_local_restore/patterns/
	"./$<" ls_etc_local_restore
	$(MAKE) run-tests

## }}}

## development {{{

.PHONY: clean
clean::
	find . -name '*.py[co]' -delete
	rm -rf *.egg *.egg-info output*/*

.PHONY: distclean
distclean:: clean
	rm -rf output*

## }}}
