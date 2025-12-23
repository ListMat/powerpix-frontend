-- Script para criar o banco de dados PostgreSQL
-- Execute este script no PostgreSQL antes de rodar a aplicação

-- Criar banco de dados (se não existir)
SELECT 'CREATE DATABASE powerpix'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'powerpix')\gexec

-- Conectar ao banco powerpix
\c powerpix

-- Criar extensões se necessário
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- O SQLAlchemy criará as tabelas automaticamente
-- Este script apenas prepara o banco

