{#
  Read every daily snapshot of one table from the Parquet data lake.

  hive_partitioning is switched off on purpose: the extractor already stores an
  `ingest_date` column inside each file, and we don't want DuckDB to add a second one
  from the folder name.
#}
{% macro read_lake(table) %}
read_parquet(
    '{{ var("parquet_dir") }}/{{ table }}/*/data.parquet',
    hive_partitioning = false,
    union_by_name = true
)
{% endmacro %}
