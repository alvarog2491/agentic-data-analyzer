# Agentic Data Analyzer

This repository creates intelligent agents to perform Exploratory Data Analysis (EDA) on datasets contained within the `data/` folder.

It leverages **Amazon Bedrock AgentCore** alongside the built-in **Code Interpreter** tool. This allows the agents to dynamically generate and execute Python code in an isolated environment to analyze the data, extract valuable insights, and perform comprehensive data exploration autonomously.

## Quick Setup Guide

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd agentic-data-analyzer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   Ensure your virtual environment is activated, then run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your data:**
   Place the datasets you wish to analyze into the `data/` directory.

5. **Run the local agent development server:**
   ```bash
   agentcore dev
   ```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
