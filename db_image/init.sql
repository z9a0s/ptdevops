CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
SELECT pg_create_physical_replication_slot('replication_slot');

\connect db_ptdevops
CREATE TABLE Phone_Numbers( ID SERIAL PRIMARY KEY, Number VARCHAR (100) NOT NULL);
CREATE TABLE Email_Addresses( ID SERIAL PRIMARY KEY, email VARCHAR (100) NOT NULL);
