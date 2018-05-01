CURL_OPTIONS ?=
CURL_URL_SERVER ?= http://localhost:9200

.DEFAULT_GOAL := all

.PHONY: all
all: mapping.json

.PHONY: FORCE_MAKE
FORCE_MAKE:

mapping.json: FORCE_MAKE
	curl $(CURL_OPTIONS) -XGET "$(CURL_URL_SERVER)/_template/logs_default" | jq '.logs_default' --sort-keys > "$@"

.PHONY: push
push: mapping.json FORCE_MAKE
	curl $(CURL_OPTIONS) -XPOST -H "Content-Type: application/json" "$(CURL_URL_SERVER)/_template/logs_default" -d "@$<"
