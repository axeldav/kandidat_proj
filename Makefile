PYTHON ?= python3.12
VENV_DIR ?= .venv
PIP := $(VENV_DIR)/bin/pip

.PHONY: venv install clean activate run fuzzy
	
run: 
	python3 checklist_chatbot.py

graph:
	python3 chatbot-graph.py

fuzzy:
	python3 fuzzy_search.py

venv:
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt

install: venv

clean:
	@rm -rf $(VENV_DIR)

activate: venv
	@echo "Starting $(SHELL) with virtual environment activated..."
	@$(SHELL) -ic '. "$(VENV_DIR)/bin/activate"; echo "Virtual environment is now active!"; exec $(SHELL)'