import * as THREE from 'https://unpkg.com/three@0.158.0/build/three.module.js';
import { GLTFLoader } from 'https://unpkg.com/three@0.158.0/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'https://unpkg.com/three@0.158.0/examples/jsm/controls/OrbitControls.js';
import { PLYExporter } from 'three/examples/jsm/exporters/PLYExporter.js';
import { GUI } from 'https://unpkg.com/dat.gui@0.7.9/build/dat.gui.module.js';

const flowerMeshes = {
  main: [],
  guest: [],
  middle1: [],
  middle2: [],
  middle3: [],
  middle4: [],
};

const branchPivots = {
  main: null,
  guest: null,
  middle1: null,
  middle2: null,
  middle3: null,
  middle4: null
};


const flowerColorOptions = {
  "桜": {
    "ブラウン": "#8b4513"
  },
  "リアトリス": {
    "パープル": "#800080",
    "ディープパープル": "#4b0082"
  },
  "ディル": {
    "ライトグリーン": "#9acd32",
    "イエローグリーン": "#adff2f"
  },
  "モルセラ": {
    "グリーン": "#00ff7f",
    "ライトグリーン": "#90ee90"
  },
  "バラ": {
    "レッド": "#ff0000",
    "ピンク": "#ffc0cb",
    "ホワイト": "#ffffff",
    "イエロー": "#ffff00",
    "オレンジ": "#ffa500",
    "パープル": "#800080",
    "ブルー（染め）": "#0037C0",
    "グリーン（染め）": "#3cb371",
    "ブラック（深赤）": "#2f0000"
  },
  "牡丹": {
    "ピンク": "#ffc0cb",
    "ホワイト": "#ffffff",
    "イエロー（希少）": "#ffffe0",
    "ブルー（染め）": "#0037C0",
  },
  "ユリ": {
    "ホワイト": "#ffffff",
    "ピンク": "#ffb6c1",
    "イエロー": "#ffff00",
    "オレンジ": "#ffa500",
    "レッド": "#ff6347",
    "ラベンダー": "#e6e6fa",
    "クリーム": "#fffdd0",
    "ブルー（染め）": "#0037C0",
  },
  "紅梅": {
    "レッド": "#ff6347",
  }
};

//Retrieve URL parameters
const params = new URLSearchParams(window.location.search);
const forcedFlower = params.get('forced_flower') || '';
const vaseName = params.get('vase') || '';
const loadingOverlay = document.getElementById('loadingOverlay');

const canvas = document.getElementById('three-canvas');
const renderer = new THREE.WebGLRenderer({ antialias: true, canvas });
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0, 0, 0);
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.5, 1500);
camera.position.set(80, 40, 80);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 2.0;
controls.dampingFactor = 0.1;

controls.enableZoom = true;
controls.zoomSpeed = 1.2;

controls.enableRotate = true;
controls.rotateSpeed = 0.8;

controls.enableDamping = true;
controls.autoRotate = false;
controls.autoRotateSpeed = 2.0;
controls.dampingFactor = 0.1;
controls.enableZoom = true;
controls.zoomSpeed = 1.2;
controls.enableRotate = true;
controls.rotateSpeed = 0.8;

//Enable auto-rotation when the "Complete" button is clicked
const completeBtn = document.getElementById('completeBtn');

completeBtn.addEventListener('click', () => {
  controls.autoRotate = true;
  completeBtn.disabled = true;
  completeBtn.textContent = '自動回転中…';
});

const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.0);
hemiLight.position.set(0, 20, 0);
const dirLight = new THREE.DirectionalLight(0xffffff, 12.0);
dirLight.position.set(10, 20, 10);
dirLight.castShadow = true;
scene.add(ambientLight, hemiLight, dirLight);

const exportGroup = new THREE.Group();
scene.add(exportGroup);

const flowerModelMapping = {
  "桜": "/static/3d/keisakura.glb",
  "リアトリス": "/static/3d/ria.glb",
  "ディル": "/static/3d/digu.glb",
  "モルセラ": "/static/3d/morusera.glb",
  "バラ": "/static/3d/rose.glb",
  "牡丹": "/static/3d/hasu.glb",
  "ユリ": "/static/3d/yuri.glb",
  //"さくら": "/static/3d/sakura2.glb",
  "紅梅": "/static/3d/morusera.glb",
  "啓扇桜": "/static/3d/morusera.glb"

};

let currentVase = null;

//Load the specified vase model and add it to the scene
function loadVase(name) {
  if (currentVase) scene.remove(currentVase);
  const vaseConfig = {
    "筒型花器": {
      path: "/static/3d/kaki2.glb",
      scale: [15, 20, 15]
    },
    "皿型花器": {
      path: "/static/3d/kaki1.glb",
      scale: [20, 10, 20]
    },
  }[name];
  if (!vaseConfig) return;
  new GLTFLoader().load(vaseConfig.path, gltf => {
    if (currentVase) scene.remove(currentVase);
    currentVase = gltf.scene;
    currentVase.scale.set(...vaseConfig.scale);
    currentVase.position.set(0, 0, 0);
    scene.add(currentVase);
  });
}

const degToRad = d => d * Math.PI / 180;

//Load a GLTF model, attach it to a pivot, and add it to the scene and exportGroup
function loadModelPromise(path, scaleVal, elevDeg, azimDeg, offsetX = 0, offsetZ = 0, branchKey) {
  return new Promise((resolve, reject) => {
    new GLTFLoader().load(
      path,
      gltf => {
        const model = gltf.scene;
        model.traverse(child => {
          if (child.isMesh) console.log(branchKey, 'mesh name:', child.name);
        });

        model.scale.set(scaleVal, scaleVal, scaleVal);
        const box = new THREE.Box3().setFromObject(model);
        model.position.y -= box.min.y;
        model.position.x += offsetX;
        model.position.z += offsetZ;
        const pivot = new THREE.Group();
        pivot.add(model);
        pivot.rotation.y = degToRad(azimDeg);
        pivot.rotation.z = degToRad(elevDeg);
        scene.add(pivot);
        exportGroup.add(pivot);
        if (branchKey) branchPivots[branchKey] = pivot;
        const meshes = [];
        model.traverse(child => {
          if (child.isMesh && child.name === 'flower') {
            // 独立した色変更を可能にするためマテリアルを複製
            child.material = child.material.clone();
            meshes.push(child);
          }
        });
        if (branchKey && flowerMeshes[branchKey]) {
          flowerMeshes[branchKey] = meshes;
        }
        resolve();
      },
      undefined,
      err => reject(err)
    );
  });
}

async function updateSceneWithOptimization(result) {
  exportGroup.clear();
  const tasks = [];
  tasks.push(
    loadModelPromise(
      flowerModelMapping[result.assignments.main],
      result.mainLen,
      result.mainElevation,
      result.mainAzimuth,
      0.1, 0,
      'main'

    )

  );
  tasks.push(
    loadModelPromise(
      flowerModelMapping[result.assignments.guest],
      result.guestLen,
      result.guestElevation,
      result.guestAzimuth,
      0, 0,
      'guest'
    )
  );
  tasks.push(
    loadModelPromise(
      flowerModelMapping[result.assignments.middle1],
      result.middle1Len,
      result.middle1Elevation,
      result.middle1Azimuth,
      0.1, 0,
      'middle1'
    )
  );
  tasks.push(
    loadModelPromise(
      flowerModelMapping[result.assignments.middle2],
      result.middle2Len,
      result.middle2Elevation,
      result.middle2Azimuth,
      0, 0.1,
      'middle2'
    )
  );
  await Promise.all(tasks);
  rebuildColorController('main', result.assignments.main);
  rebuildColorController('guest', result.assignments.guest);
  rebuildColorController('middle1', result.assignments.middle1);
  rebuildColorController('middle2', result.assignments.middle2);

  angleParams.mainAz = result.mainAzimuth;
  angleParams.mainEl = result.mainElevation;
  angleParams.guestAz = result.guestAzimuth;
  angleParams.guestEl = result.guestElevation;
  angleParams.mid1Az = result.middle1Azimuth;
  angleParams.mid1El = result.middle1Elevation;
  angleParams.mid2Az = result.middle2Azimuth;
  angleParams.mid2El = result.middle2Elevation;

  angleFolder.updateDisplay();
}

function clearScene() {
  scene.clear();
  scene.add(ambientLight, hemiLight, dirLight);
  if (currentVase) scene.add(currentVase);
  scene.add(exportGroup);

}

function exportPointCloud(arr_id) {
  exportGroup.updateMatrixWorld(true);
  const exporter = new PLYExporter();
  exporter.parse(
    exportGroup,
    plyText => {
      console.log('PLY length:', plyText.length);
      fetch(`/upload_pointcloud?arr_id=${arr_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: plyText
      })
        .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
        .then(data => console.log('upload ok', data))
        .catch(console.error);
    },
    { binary: false, excludeAttributes: ['normal', 'uv', 'color'], excludeIndices: true }
  );
}

//Fetch optimization results from the server and update the scene
async function runOptimization(forced) {
  try {
    const res = await fetch(
      `/optimize?forced_flower=${encodeURIComponent(forced)}&vase=${encodeURIComponent(vaseName)}`);
    const result = await res.json();
    if (result.error) throw new Error(result.error);

    clearScene();
    await updateSceneWithOptimization(result);

    const ext = await runExtendOptimization(result);
    if (result.arr_id) exportPointCloud(result.arr_id);
    rebuildColorController('middle3', ext.assignments.middle3);
    rebuildColorController('middle4', ext.assignments.middle4);
  } catch (err) {
    console.error(err);
  } finally {
    loadingOverlay.style.display = 'none';
  }
}
const gui = new GUI();
const colorParams = {
  main: '#ff69b4',
  guest: '#ffa500',
  middle1: '#90ee90',
  middle2: '#add8e6',
  middle3: '#90ee90',
  middle4: '#add8e6'
};

function updateFlowerColor(branchKey, colorHex) {
  const meshes = flowerMeshes[branchKey];
  if (!meshes) return;
  meshes.forEach(mesh => {
    mesh.material.color.set(colorHex);
    mesh.material.needsUpdate = true;
  });
}

let guiControllers = {
  main: null,
  guest: null,
  middle1: null,
  middle2: null,
  middle3: null,
  middle4: null
};

function rebuildColorController(branchKey, flowerName) {
  if (guiControllers[branchKey]) {
    gui.remove(guiControllers[branchKey]);
    guiControllers[branchKey] = null;
  }

  const opts = flowerColorOptions[flowerName] || {};
  const names = Object.keys(opts);
  if (names.length === 0) return;
  colorParams[branchKey] = opts[names[0]];

  guiControllers[branchKey] = gui
    .add(colorParams, branchKey, names)
    .name(`${branchKey} の色`)
    .onChange(key => {
      const hex = opts[key];
      updateFlowerColor(branchKey, hex);
    });
}


const angleParams = {
  mainAz: 0, mainEl: 0,
  guestAz: 0, guestEl: 0,
  mid1Az: 0, mid1El: 0,
  mid2Az: 0, mid2El: 0,
  mid3Az: 0, mid3El: 0,
  mid4Az: 0, mid4El: 0
};

const angleFolder = gui.addFolder('枝ごとの角度調整');

angleFolder
  .add(angleParams, 'mainAz', 0, 0).name('主枝 方位').onChange(v => {
    branchPivots.main.rotation.y = degToRad(v);
  });
angleFolder
  .add(angleParams, 'mainEl', -20, 20).name('主枝 高度').onChange(v => {
    branchPivots.main.rotation.z = degToRad(v);
  });

angleFolder
  .add(angleParams, 'guestAz', 0, 0).name('客枝 方位').onChange(v => {
    branchPivots.guest.rotation.y = degToRad(v);
  });
angleFolder
  .add(angleParams, 'guestEl', 0, 0).name('客枝 高度').onChange(v => {
    branchPivots.guest.rotation.z = degToRad(v);
  });

angleFolder
  .add(angleParams, 'mid1Az', -120, 120).name('中間1 方位').onChange(v => {
    branchPivots.middle1.rotation.y = degToRad(v);
  });
angleFolder
  .add(angleParams, 'mid1El', 0, 45).name('中間1 高度').onChange(v => {
    branchPivots.middle1.rotation.z = degToRad(v);
  });

angleFolder
  .add(angleParams, 'mid2Az', -120, 120).name('中間2 方位').onChange(v => {
    branchPivots.middle2.rotation.y = degToRad(v);
  });
angleFolder
  .add(angleParams, 'mid2El', 0, 45).name('中間2 高度').onChange(v => {
    branchPivots.middle2.rotation.z = degToRad(v);
  });

angleFolder
  .add(angleParams, 'mid3Az', -120, 120).name('中間3 方位').onChange(v => {
    branchPivots.middle3.rotation.y = degToRad(v);
  });
angleFolder
  .add(angleParams, 'mid3El', 0, 45).name('中間3 高度').onChange(v => {
    branchPivots.middle3.rotation.z = degToRad(v);
  });

angleFolder
  .add(angleParams, 'mid4Az', -120, 120).name('中間4 方位').onChange(v => {
    branchPivots.middle4.rotation.y = degToRad(v);
  });
angleFolder
  .add(angleParams, 'mid4El', 0, 45).name('中間4 高度').onChange(v => {
    branchPivots.middle4.rotation.z = degToRad(v);
  });

angleFolder.open();


async function runExtendOptimization(baseResult) {
  const res = await fetch('/optimize_extend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      arr_id: baseResult.arr_id,
      base_assignments: baseResult.assignments,
      base_lengths: {
        main: baseResult.mainLen,
        guest: baseResult.guestLen,
        middle1: baseResult.middle1Len,
        middle2: baseResult.middle2Len
      },
      base_angles: {
        mainAzimuth: baseResult.mainAzimuth,
        mainElevation: baseResult.mainElevation,
        guestAzimuth: baseResult.guestAzimuth,
        guestElevation: baseResult.guestElevation,
        middle1Azimuth: baseResult.middle1Azimuth,
        middle1Elevation: baseResult.middle1Elevation,
        middle2Azimuth: baseResult.middle2Azimuth,
        middle2Elevation: baseResult.middle2Elevation
      }
    })
  });
  const ext = await res.json();

  await loadModelPromise(
    flowerModelMapping[ext.assignments.middle3],
    ext.lengths.middle3,
    ext.angles.middle3Elevation,
    ext.angles.middle3Azimuth,
    0, 0,
    'middle3'
  );
  await loadModelPromise(
    flowerModelMapping[ext.assignments.middle4],
    ext.lengths.middle4,
    ext.angles.middle4Elevation,
    ext.angles.middle4Azimuth,
    0, 0,
    'middle4'
  );
  rebuildColorController('middle3', ext.assignments.middle3);
  rebuildColorController('middle4', ext.assignments.middle4);
  return ext;
}

loadVase(vaseName);
runOptimization(forcedFlower);

// Adjust camera and renderer on window resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Main render loop
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();

