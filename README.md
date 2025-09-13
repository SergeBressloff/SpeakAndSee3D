# Speak & See 3D

Speak & See 3D is an innovative application that generates 3D assets from natural language prompts. Designed for accessibility and creative content generation, it integrates speech transcription, text-to-image diffusion, and image-to-3D reconstruction in a modular pipeline for ease of use and extensibility.

## Table of Contents

- [Features](#features)
- [Motivation & Accessibility](#motivation--accessibility)
- [Architecture](#architecture)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contact](#contact)

## Features

- **Natural Language to 3D Asset Creation**: Generate 3D models by describing them in speech or text.
- **Modular Pipeline**: Independent executables for each stage—speech transcription, text-to-image diffusion, and image-to-3D reconstruction.
- **Locally Executed AI**: No reliance on cloud infrastructure; runs efficiently on consumer hardware.
- **Accessible Frontend**: PySide6-based desktop interface, with embedded Three.js viewer for smooth 3D rendering and interaction.
- **Extensible**: Easily swap or upgrade diffusion techniques and pipeline modules.

## Motivation & Accessibility

A key goal for Speak & See 3D is accessibility. Developed in consultation with the National Autistic Society, the application supports inclusive content creation in education, especially for students on the autism spectrum who benefit from visual learning. Its potential extends to general educational tools and creative industries.

## Architecture

- **Pipeline Components**: Independently compiled Python executables (via Nuitka), each handling a separate stage:
  - Speech transcription
  - Text-to-image diffusion
  - Image-to-3D reconstruction
- **Frontend**: Built with PySide6 for a native desktop experience.
- **3D Viewer**: Embedded Three.js renderer for interactive asset viewing.

## Usage

1. **Describe a Model**: Type or speak a description of the 3D asset you want to create (e.g., "elephant", "a tree", "3D model of a dinosaur").
2. **Generate**: Click "Generate" to start the pipeline.
3. **View & Interact**: The generated 3D model appears in the embedded viewer; interact with it directly in the app.

## Screenshots

- **Main Interface**  
  ![image1](image1)

- **Generated Elephant Model**  
  ![image2](image2)

- **Generated Tree Model**  
  ![image3](image3)

## Contact

Serge Bressloff  
For questions, feedback, or collaboration inquiries, please contact via GitHub [SergeBressloff](https://github.com/SergeBressloff).
