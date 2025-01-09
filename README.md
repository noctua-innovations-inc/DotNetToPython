# Llama 3.2 3B Instruct Integration with C#

This project demonstrates how to integrate **Meta's Llama 3.2 3B Instruct** model into a C# application using a Python gRPC server as the backend.
The goal is to leverage AI to generate as much of the solution code as possible, showcasing the capabilities of large language models in real-world applications.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Contributing](#contributing)
4. [License](#license)

---

## Overview

The project consists of two components:
1. **Python Server Backend**:
   - A RabbitMQ server that hosts the **Llama 3.2 3B Instruct** model.
   - The server receives text prompts from the C# client, generates responses using the model, and returns the results.

2. **C# Console Frontend**:
   - A console application that interacts with the Python RabbitMQ server.
   - Users can input prompts, and the application displays the AI-generated responses.

The objective is to use AI to write as much of the solution code as possible, demonstrating the power of large language models in automating development tasks.

---

## Prerequisites

### Python Server Backend
- Python 3.12 (see environment.yml)
- GPU with CUDA support (recommended for faster inference)
- Hugging Face `transformers` library
- RabbitMQ through `pica` library

### C# Console Frontend
- .NET 8 SDK
- RabbitMQ and `RabbitMQ.Client` libraries

---

## Contributing

Contributions are welcome! If you'd like to improve the project, please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE.txt](LICENSE.txt) file for details.

---

## Acknowledgments

- **Meta AI** for developing the Llama 3.2 3B Instruct model.
- **Hugging Face** for providing the `transformers` library.
- **gRPC** for enabling seamless communication between the Python server and C# client.
- **RabbitMQ** for enabling seamless communications between the Python server and C# client
