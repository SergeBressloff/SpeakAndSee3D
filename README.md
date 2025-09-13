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

<img src="https://github.com/user-attachments/assets/71625d50-c0e8-4e56-b1fb-8d1e339c15a7" alt="Pipeline Overview" width="500"/>

- **Frontend**: Built with PySide6 for a native desktop experience.
- **3D Viewer**: Embedded Three.js renderer for interactive asset viewing.

<img src="https://github.com/user-attachments/assets/ac40f135-a8fd-419b-98ae-93a488c5bdf9" alt="Frontend Overview" width="500"/>

## Usage

1. **Describe a Model**: Type or speak a description of the 3D asset you want to create (e.g., "elephant", "a tree", "a human heart").
2. **Generate**: Click "Generate" to start the pipeline.
3. **View & Interact**: The generated 3D model appears in the embedded viewer; interact with it directly in the app.

## Screenshots

<img src="https://github.com/user-attachments/assets/9ee29a5c-dd5c-4bfb-8c09-7c286d1b2fb4" alt="Main Interface" width="400"/>
<img src="https://github.com/user-attachments/assets/65d31457-cd14-4b31-90e8-41955f36b696" alt="Heart Model" width="400" />
<img src="https://github.com/user-attachments/assets/53c492ba-312b-4aea-a7c9-ced948185f6c" alt="Elephant Model" width="400"/>
<img src="https://github.com/user-attachments/assets/37ab1e19-3db6-464d-90fc-3e5ebc34a511" alt="Tree Model" width="400"/>

## Contact

Serge Bressloff  
For questions, feedback, or collaboration inquiries, please contact via GitHub [SergeBressloff](https://github.com/SergeBressloff).
