FROM metabase/metabase:v0.49.8

USER root

RUN mkdir -p /plugins && \
    curl -L -o /plugins/duckdb.metabase-driver.jar \
    https://github.com/MotherDuck-open-source/metabase-duckdb-driver/releases/download/0.2.9/duckdb.metabase-driver.jar && \
    chmod 644 /plugins/duckdb.metabase-driver.jar
