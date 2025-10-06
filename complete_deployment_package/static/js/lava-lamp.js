// WebGL Shader-Based Lava Lamp Metaballs - Enhanced Realistic 3D
(function() {
  const canvas = document.getElementById('lava-lamp-canvas');
  let gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) {
    canvas.style.display = 'none';
    return;
  }

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
  window.addEventListener('resize', resize);
  resize();

  // Vertex shader (simple passthrough)
  const vertSrc = `
    attribute vec2 a_position;
    varying vec2 v_uv;
    void main() {
      v_uv = (a_position + 1.0) * 0.5;
      gl_Position = vec4(a_position, 0, 1);
    }
  `;

  // Fragment shader (enhanced realistic 3D metaballs)
  const fragSrc = `
    precision highp float;
    #define BLOB_COUNT 12
    varying vec2 v_uv;
    uniform float u_time;
    uniform vec2 u_resolution;
    uniform vec3 u_colors[BLOB_COUNT];
    uniform vec3 u_blobPos[BLOB_COUNT]; // xy: pos, z: radius
    uniform vec3 u_blobVel[BLOB_COUNT]; // xy: velocity, z: depth
    
    // Noise functions for organic variation
    float hash(vec2 p) {
      return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
    }
    
    float noise(vec2 p) {
      vec2 i = floor(p);
      vec2 f = fract(p);
      f = f * f * (3.0 - 2.0 * f);
      return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
                 mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
    }
    
    float fbm(vec2 p) {
      float value = 0.0;
      float amplitude = 0.5;
      float frequency = 1.0;
      for (int i = 0; i < 4; i++) {
        value += amplitude * noise(p * frequency);
        amplitude *= 0.5;
        frequency *= 2.0;
      }
      return value;
    }
    
    void main() {
      vec2 uv = v_uv * u_resolution;
      float field = 0.0;
      vec3 color = vec3(0.0);
      float total = 0.0;
      float depth = 0.0;
      
      // Calculate enhanced metaball field with depth
      for (int i = 0; i < BLOB_COUNT; i++) {
        vec2 pos = u_blobPos[i].xy;
        float r = u_blobPos[i].z;
        float blobDepth = u_blobVel[i].z; // Using velocity.z for depth
        
        float dx = uv.x - pos.x;
        float dy = uv.y - pos.y;
        float dist = sqrt(dx * dx + dy * dy);
        
        // Enhanced metaball function with depth influence
        float depthFactor = 1.0 + blobDepth * 0.3;
        float adjustedR = r * depthFactor;
        float v = adjustedR * adjustedR / (dist * dist + 1.0);
        
        // Add surface tension effect
        float surfaceTension = smoothstep(0.0, adjustedR * 0.3, dist) * smoothstep(adjustedR, adjustedR * 0.7, dist);
        v *= (1.0 + surfaceTension * 0.2);
        
        field += v;
        color += u_colors[i] * v;
        total += v;
        depth = max(depth, blobDepth * v);
      }
      
      // Normalize color
      color = color / max(total, 0.001);
      
             // Enhanced lighting with depth-based effects - more opaque
       float alpha = smoothstep(0.8, 1.8, field);
      
             // Darker inner glow with depth (no white)
       float innerGlow = smoothstep(1.8, 2.5, field);
       float depthGlow = smoothstep(0.0, 0.5, depth);
       color = mix(color, color * 1.5, innerGlow * 0.2 * (1.0 + depthGlow * 0.3));
      
             // Solid edges with minimal glow
       float outerGlow = smoothstep(0.7, 1.1, field);
       color = mix(color, color * 0.8, outerGlow * 0.2);
      
             // Minimal surface detail - ultra slow and fluid
       vec2 detailUV = uv * 0.02 + u_time * 0.00005; // Much slower and smoother
       float surfaceDetail = fbm(detailUV) * 0.003; // Much smaller
       color += vec3(surfaceDetail * 0.001); // Much smaller
       
       // Add depth-based shadows (darker and more solid)
       float shadow = smoothstep(0.0, 0.3, depth) * 0.35; // Stronger shadows for solid look
       color *= (1.0 - shadow);
       
       // No center light source - removed highlights
       
       // Minimal organic variation - ultra slow and fluid
       float organicNoise = fbm(uv * 0.01 + u_time * 0.00002); // Much slower and smoother
       color += vec3(organicNoise * 0.0005); // Much smaller
      
             // Ensure colors stay in lineage color range with darker constraints
       color = clamp(color, vec3(0.02, 0.02, 0.02), vec3(0.8, 0.8, 0.8));
      
             // Remove transparency for solid opaque look
       alpha = clamp(alpha, 0.0, 1.0);
       
       gl_FragColor = vec4(color, alpha * 0.95);
    }
  `;

  function createShader(type, src) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, src);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(shader));
    }
    return shader;
  }

  function createProgram(vs, fs) {
    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(prog));
    }
    return prog;
  }

  const vertShader = createShader(gl.VERTEX_SHADER, vertSrc);
  const fragShader = createShader(gl.FRAGMENT_SHADER, fragSrc);
  const program = createProgram(vertShader, fragShader);
  gl.useProgram(program);

  // Fullscreen quad
  const posBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
    -1, -1, 1, -1, -1, 1,
    -1, 1, 1, -1, 1, 1
  ]), gl.STATIC_DRAW);
  const posLoc = gl.getAttribLocation(program, 'a_position');
  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

  // Uniform locations
  const u_time = gl.getUniformLocation(program, 'u_time');
  const u_resolution = gl.getUniformLocation(program, 'u_resolution');
  const u_colors = gl.getUniformLocation(program, 'u_colors');
  const u_blobPos = gl.getUniformLocation(program, 'u_blobPos');
  const u_blobVel = gl.getUniformLocation(program, 'u_blobVel');

  // Blob parameters with enhanced physics
  const BLOB_COUNT = 12;
  // Vibrant lava lamp colors - classic neon colors
  const baseColors = [
    [1.0, 0.0, 1.0],    // Magenta - vibrant pink
    [1.0, 0.27, 0.0],   // Orange Red - bright orange
    [0.0, 1.0, 1.0],    // Cyan - electric blue
    [1.0, 1.0, 0.0],    // Yellow - bright yellow
    [1.0, 0.08, 0.58],  // Deep Pink - hot pink
    [0.0, 1.0, 0.5],    // Spring Green - neon green
    [0.54, 0.17, 0.89], // Blue Violet - purple
    [1.0, 0.5, 0.0],    // Orange - bright orange
    [0.5, 0.0, 1.0],    // Purple - vibrant purple
    [0.0, 0.8, 1.0],    // Sky Blue - light blue
    [1.0, 0.0, 0.5],    // Rose - pink rose
    [0.0, 1.0, 0.0]     // Lime - bright green
  ];
  
  const blobs = [];
  for (let i = 0; i < BLOB_COUNT; i++) {
    blobs.push({
      x: Math.random(),
      y: -0.1 + Math.random() * 0.1,
      vx: 0,
      vy: 0,
      radius: 0.06 + Math.random() * 0.1, // Smaller size variation
      depth: Math.random() * 0.6 + 0.3, // More depth variation
      mass: 0.5 + Math.random() * 0.8, // More mass variation
      movePhase: Math.random() * Math.PI * 2,
      pulsePhase: Math.random() * Math.PI * 2,
      wobblePhase: Math.random() * Math.PI * 2, // New wobble phase
      morphPhase: Math.random() * Math.PI * 2, // New morphing phase
      startTime: 0,
      lastUpdate: 0,
      personality: Math.random() // Unique personality for each blob
    });
  }

  function animate() {
    const t = performance.now() * 0.001;
    const dt = Math.min(0.016, t - (blobs[0].lastUpdate || t)); // Cap delta time
    
    gl.uniform1f(u_time, t);
    gl.uniform2f(u_resolution, canvas.width, canvas.height);
    
    // Enhanced blob physics with realistic movement
    const blobPos = [];
    const blobVel = [];
    
    for (let i = 0; i < BLOB_COUNT; i++) {
      const blob = blobs[i];
      if (blob.startTime === 0) blob.startTime = t;
      if (blob.lastUpdate === 0) blob.lastUpdate = t;
      
      // Apply physics forces - ultra slow and fluid
      const gravity = 0.000001 * blob.mass; // Much slower and smoother
      const drag = 0.9998; // More resistance for fluid movement
      const buoyancy = 0.0000003 * blob.mass; // Much slower
      
      // Add organic forces - ultra slow and fluid
      const organicForceX = Math.sin(t * 0.0002 + blob.movePhase + i) * 0.0000002; // Much slower
      const organicForceY = Math.cos(t * 0.00015 + blob.movePhase + i) * 0.0000001; // Much slower
      
      // Update velocity with realistic physics
      blob.vy += gravity - buoyancy;
      blob.vx += organicForceX;
      blob.vy += organicForceY;
      
      // Apply drag
      blob.vx *= drag;
      blob.vy *= drag;
      
      // Update position
      blob.x += blob.vx * dt * 1000;
      blob.y += blob.vy * dt * 1000;
      
      // Boundary constraints with ultra smooth bouncing
      if (blob.x < 0.1) {
        blob.x = 0.1;
        blob.vx *= -0.05; // Ultra gentle bounce
      } else if (blob.x > 0.9) {
        blob.x = 0.9;
        blob.vx *= -0.05; // Ultra gentle bounce
      }
      
      if (blob.y > 1.1) {
        blob.y = -0.1 + Math.random() * 0.1;
        blob.vy = 0;
        blob.vx = 0;
        blob.startTime = t;
      }
      
             // Add subtle depth variation - ultra slow and fluid
       blob.depth += Math.sin(t * 0.0005 + i) * 0.000001; // Much slower and smoother
       blob.depth = Math.max(0.3, Math.min(1.0, blob.depth));
       
       // Pulsing radius with organic variation - ultra slow and fluid
       const pulse = Math.sin(t * 0.0008 + blob.pulsePhase + i) * 0.0002; // Much slower and smoother
       const organicPulse = Math.cos(t * 0.0006 + i) * 0.0001; // Much slower and smoother
       const radius = blob.radius + pulse + organicPulse;
      
      blobPos.push(blob.x * canvas.width, blob.y * canvas.height, radius * Math.min(canvas.width, canvas.height));
      blobVel.push(blob.vx * 100, blob.vy * 100, blob.depth);
      
      blob.lastUpdate = t;
    }
    
              // Solid colors - no animation
     const colors = baseColors.map((c, i) => {
       return [c[0], c[1], c[2]]; // Use solid colors without any variation
     });
    
    gl.uniform3fv(u_colors, colors.flat());
    gl.uniform3fv(u_blobPos, blobPos);
    gl.uniform3fv(u_blobVel, blobVel);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    requestAnimationFrame(animate);
  }

  // HSL to RGB for color animation
  function hslToRgb(h, s, l) {
    let r, g, b;
    if (s == 0) { r = g = b = l; }
    else {
      function hue2rgb(p, q, t) {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      }
      let q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      let p = 2 * l - q;
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }
    return [r, g, b];
  }

  animate();
})(); 