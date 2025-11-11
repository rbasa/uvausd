

create table fx_rate (
  DATE DATE NOT NULL,
  pair varchar(10) NOT NULL,
  kind varchar(10) NOT NULL,
  rate decimal(10, 8),
  PRIMARY KEY (DATE, pair),
  FOREIGN KEY (pair) REFERENCES pair(pair)
);

create table pair(
  pair varchar(10) PRIMARY KEY,
  description text NOT NULL
);

insert into pair (pair, description) values 
('USD_ARS', 'Dólar Oficial medido en pesos argentinos'),
('USDM_ARS', 'Dólar MEP medido en pesos argentinos'),
('USDB_ARS', 'Dólar Blue medido en pesos argentinos'),
('USDC_ARS', 'Dólar Cripto medido en pesos argentinos'),
('UVA_ARS', 'UVA medida en pesos argentinos'),
('UVA_USD', 'UVA medida en dólares estadounidenses'),
('UVA_USDM', 'UVA medida en dólares mep'),
('UVA_USDB', 'UVA medida en dólares blue'),
('UVA_USDC', 'UVA medida en dólares cripto');