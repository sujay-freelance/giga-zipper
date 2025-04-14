IMAGE_NAME=zip-tool
TAG=latest
FULL_IMAGE=$(IMAGE_NAME):$(TAG)
CONTAINER_INPUT=/app/data/input
CONTAINER_OUTPUT=/app/data/zips/output.zip

build:
	docker build -t $(FULL_IMAGE) .

run:
	@mkdir -p data/zips
	docker run --rm -v "$$PWD:/app" $(FULL_IMAGE) $(CONTAINER_INPUT) $(CONTAINER_OUTPUT) --verify

test:
	@echo "Running demo test..."
	mkdir -p data/input && echo "sample data" > data/input/file.txt
	make run

generate:
	@mkdir -p data/input
	python3 generate-test-files.py data/input/large_file.test --size-gb=10 --fast

validate:
	@echo "Validating extracted data..."
	rm -rf data/unzipped && mkdir -p data/output
	unzip -q data/zips/output.zip -d data/output
	diff -r data/input data/output && echo "✅ Data matched" || echo "❌ Data mismatch"

push:
	docker tag $(FULL_IMAGE) sujaykumarsuman/$(FULL_IMAGE)
	docker push sujaykumarsuman/$(FULL_IMAGE)

clean:
	rm -rf data/zips data/output data/input *.zip *.txt