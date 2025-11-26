PROJECT_NAME = test-capacity-app

DC = docker-compose
DC_FILE = docker-compose.yml

BACKEND_SERVICE = backend
FRONTEND_SERVICE = frontend
MONGO_SERVICE = mongo

.PHONY: help up down restart build logs logs-backend logs-frontend logs-mongo sh-backend sh-frontend sh-mongo ps

help:
	@echo "Makefile for $(PROJECT_NAME)"
	@echo ""
	@echo "Usage:"
	@echo "  make up             Start all services (docker-compose up -d)"
	@echo "  make down           Stop and remove all services"
	@echo "  make restart        Restart all services"
	@echo "  make build          Build all images"
	@echo "  make logs           Tail logs for all services"
	@echo "  make logs-backend   Tail logs for backend service"
	@echo "  make logs-frontend  Tail logs for frontend service"
	@echo "  make logs-mongo     Tail logs for mongo service"
	@echo "  make sh-backend     Open a shell inside backend container"
	@echo "  make sh-frontend    Open a shell inside frontend container"
	@echo "  make sh-mongo       Open a shell inside mongo container"
	@echo "  make ps             Show container status"

up:
	$(DC) -f $(DC_FILE) up -d

up-build:
	$(DC) -f $(DC_FILE) up --build
down:
	$(DC) -f $(DC_FILE) down

restart: down up

build:
	$(DC) -f $(DC_FILE) build

build-front:
	$(DC) build $(FRONTEND_SERVICE)

logs:
	$(DC) -f $(DC_FILE) logs -f

logs-backend:
	$(DC) -f $(DC_FILE) logs -f $(BACKEND_SERVICE)

logs-frontend:
	$(DC) -f $(DC_FILE) logs -f $(FRONTEND_SERVICE)

logs-mongo:
	$(DC) -f $(DC_FILE) logs -f $(MONGO_SERVICE)

sh-backend:
	winpty $(DC) -f $(DC_FILE) exec $(BACKEND_SERVICE) bash

sh-frontend:
	winpty $(DC) -f $(DC_FILE) exec $(FRONTEND_SERVICE) sh

sh-mongo:
	winpty $(DC) -f $(DC_FILE) exec $(MONGO_SERVICE) bash
ps:
	$(DC) -f $(DC_FILE) ps
