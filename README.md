# 🌸 Japanese flower arrangement 3D Optimizer & Viewer

A web application that uses quantum-inspired optimization to design and visualize 3D Japanese flower arrangement compositions. The system generates optimal flower placements based on aesthetic constraints and displays the result in a browser using Three.js.

## ✨ Features

- 🔢 **QUBO-based Optimization**: Uses OpenJij to model and solve the flower positioning problem
- 🧠 **Automatic Layout**: Computes ideal branch lengths and angles based on vase size and floral materials
- 🌐 **Web Viewer**: Interactive 3D visualization of the ikebana arrangement (GLTF support)
- 🗃️ **Database Integration**: Stores each arrangement and branch data for later retrieval
- ☁️ **Point Cloud Upload**: Accepts 3D scans (.ply) and extracts geometric features
- 🚀 **Extendable**: Supports adding extra branches through secondary optimization