.PHONY: lint lint-style lint-mypy lint-release
.PHONY: format
.PHONY: test docker-test docker-build-test
.PHONY: docs


add_cwd_to_path = PATH=$(shell pwd):$${PATH} PYTHONPATH=$(shell pwd):$${PYTHONPATH}


# --------------Lint-------------- #


LINT = $(shell pwd)


lint : lint-style lint-mypy


lint-style :
	@echo 'Checking codestyle...'
	@flake8 $(LINT) \
		&& python tools/lint_trailing_comma.py $(shell find $(LINT) -type f -name "*.py")
	@echo 'No issues'

lint-mypy :
	@echo 'Running static type checker...'
	@mypy $(LINT)
	@echo 'No issues'


git_branch = $(shell git rev-parse --abbrev-ref HEAD)
git_version = $(shell git describe --tags --abbrev=0)
marsh_version = $(shell python tools/find_version.py marsh/__init__.py)


lint-release :
	@echo 'Checking branch...'
	@if [ "$(git_branch)" != "main" ]; \
	then \
		echo 'Error: not on main branch'; \
		exit 1; \
	fi;
	@echo 'Checking version...'
	@if [ "$(git_version)" != "v$(marsh_version)" ]; \
	then \
		printf 'Error: git tag "$(git_version)" mismatch with marsh version "v$(marsh_version)"\n'; \
		exit 1; \
	fi;
	@echo 'No issues'


# --------------Format-------------- #


FORMAT = $(shell pwd)


format :
	@add-trailing-comma \
		--py36-plus \
		--exit-zero-even-if-changed \
		$(shell find $(FORMAT) -type f -name "*.py")


# --------------Testing-------------- #


TEST = test


test :
	@$(add_cwd_to_path) pytest $(TEST)


DOCKER_PYTHON_VERSION := 3.8
DOCKER_TEST_FILE      := test/Dockerfile
DOCKER_TEST_NAME      := marsh/test/py${DOCKER_PYTHON_VERSION}
DOCKER_TEST_TAG       := $$(git rev-parse HEAD)
DOCKER_TEST_IMG       := ${DOCKER_TEST_NAME}:${DOCKER_TEST_TAG}
DOCKER_TEST_LATEST    := ${DOCKER_TEST_NAME}:latest


docker-build-test :
	@docker build \
		--build-arg PYTHON_VERSION=$(DOCKER_PYTHON_VERSION) \
		-t ${DOCKER_TEST_IMG} \
		-f ${DOCKER_TEST_FILE} \
		.
	@docker tag ${DOCKER_TEST_IMG} ${DOCKER_TEST_LATEST}


docker-test :
	@if [ "$$(docker images -q $(DOCKER_TEST_LATEST) 2> /dev/null)" == "" ]; \
	then \
		$(MAKE) docker-build-test DOCKER_PYTHON_VERSION=$(DOCKER_PYTHON_VERSION); \
	fi;
	@docker run --rm -v $(shell pwd):/marsh $(DOCKER_TEST_LATEST) pytest ${TEST}



# --------------Docs-------------- #

docs :
	-@rm -r docs/build &> /dev/null || exit 0
	@$(add_cwd_to_path) python docs/source/scripts/build_supported_types.py
	@$(add_cwd_to_path) sphinx-build docs/source -W docs/build/html
