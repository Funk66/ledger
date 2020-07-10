-- When withdrawing money, add transaction of +money to cash account
-- to keep saldo

CREATE TABLE IF NOT EXISTS transactions (
  "date" DATE NOT NULL,
  "valuta" DATE,
  "type" TEXT NOT NULL,
  "subject" TEXT NOT NULL,
  "reference" TEXT NOT NULL,
  "value" FLOAT NOT NULL,
  "saldo" FLOAT NOT NULL,
  "account" TEXT NOT NULL,
  "category" TEXT,
  "comment" TEXT,
  PRIMARY KEY("date", "value", "saldo", "account")
  );

CREATE TABLE IF NOT EXISTS tags (
  "name" TEXT NOT NULL,
  "transaction" TEXT NOT NULL,
  FOREIGN KEY("transaction") REFERENCES transactions("hash"),
  PRIMARY KEY("name", "transaction")
  )
