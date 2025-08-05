import * as THREE from './three.module.js';
import { GLTFLoader } from './GLTFLoader.js';
import { OBJLoader } from './OBJLoader.js'
import { OrbitControls } from './OrbitControls.js';

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x222222);
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.minDistance = 0.5;
controls.maxDistance = 100;

// Lighting
scene.add(new THREE.AmbientLight(0xffffff, 0.6));
scene.add(new THREE.DirectionalLight(0xffffff, 0.6));

// Loader
const gltfLoader = new GLTFLoader();
const objLoader = new OBJLoader();
let currentModel = null;

function loadModel(filePath) {
    const extension = filePath.split('.').pop().toLowerCase();

    // Remove any previous model
    if (currentModel) {
        scene.remove(currentModel);
        currentModel = null;
    }

    if (extension === 'glb' || extension === 'gltf') {
        gltfLoader.load(
            filePath,
            (gltf) => {
                currentModel = gltf.scene;
                scene.add(currentModel);
                centerAndPositionModel(currentModel);
            },
            undefined,
            (error) => {
                console.error("Failed to load GLB/GLTF model:", error);
            }
        );
    } else if (extension === 'obj') {
        objLoader.load(
            filePath,
            (obj) => {
                currentModel = obj;
                scene.add(currentModel);
                centerAndPositionModel(currentModel);
            },
            undefined,
            (error) => {
                console.error("Failed to load OBJ model:", error);
            }
        );
    } else {
        console.error("Unsupported model format:", extension);
    }
}

function centerAndPositionModel(model) {
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3()).length();
    const center = box.getCenter(new THREE.Vector3());

    // rotate model
    model.rotation.x = -Math.PI / 2;
    model.rotation.z = -Math.PI;

    model.position.sub(center);
    camera.position.set(0, 0, size * 0.8);
    camera.lookAt(0, 0, 0);
    controls.update();
}

// Expose globally so Python can call it
window.loadModel = loadModel;

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();

// Responsive resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
