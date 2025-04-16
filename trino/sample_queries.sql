show tables in iceberg_datalake.default;

select * from iceberg_datalake.default.employees;
select * from iceberg_datalake.default.clients;
select * from iceberg_datalake.default.sessions;

select count(*) from iceberg_datalake.default.sessions;
select count(distinct uuid) from iceberg_datalake.default.sessions;


select count(*) from iceberg_datalake.default.employees;
select count(distinct uuid) from iceberg_datalake.default.employees;

select count(*) from iceberg_datalake.default.clients;
select count(distinct uuid) from iceberg_datalake.default.clients;




SELECT COUNT(*) FROM iceberg_datalake.default."employees$files";
SELECT COUNT(*) FROM iceberg_datalake.default."employees$snapshots";
SELECT COUNT(*) FROM iceberg_datalake.default."clients$files";
SELECT COUNT(*) FROM iceberg_datalake.default."clients$snapshots";

SELECT COUNT(*) FROM iceberg_datalake.default."sessions$files";
SELECT COUNT(*) FROM iceberg_datalake.default."sessions$snapshots";



show create table iceberg_datalake.default.sessions;