import React, { useEffect, useRef } from 'react'

export default function VectraCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (!gl) {
      canvas.style.background = 'radial-gradient(circle at 50% 30%, rgba(234, 88, 12, 0.05), transparent 70%)'
      return
    }

    let animationFrameId
    let startTime = Date.now()
    let mouseX = 0.5
    let mouseY = 0.5

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect()
      mouseX = (e.clientX - rect.left) / rect.width
      mouseY = 1.0 - (e.clientY - rect.top) / rect.height
    }

    window.addEventListener('mousemove', handleMouseMove)

    // Shaders
    const vsrc = `
      attribute vec2 position;
      void main() {
        gl_Position = vec4(position, 0.0, 1.0);
      }
    `

    const fsrc = `
      precision highp float;
      uniform vec2 u_res;
      uniform float u_time;
      uniform vec2 u_mouse;

      float hash(vec2 p) {
        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
      }

      void main() {
        vec2 uv = gl_FragCoord.xy / u_res;
        float aspect = u_res.x / u_res.y;
        vec2 st = uv;
        st.x *= aspect;

        // Interactive mouse parallax drift
        vec2 m = u_mouse * vec2(aspect, 1.0);
        st += (m - 0.5 * vec2(aspect, 1.0)) * 0.04;

        float t = u_time * 0.15;

        // Subtle geometric grid lattice
        vec2 grid = fract(st * 16.0);
        float lineX = smoothstep(0.02, 0.0, grid.x) + smoothstep(0.98, 1.0, grid.x);
        float lineY = smoothstep(0.02, 0.0, grid.y) + smoothstep(0.98, 1.0, grid.y);
        float gridLine = max(lineX, lineY);

        // Slow breathing pulse
        float pulse = sin(t * 1.5) * 0.5 + 0.5;

        // Ambient radial illumination near top center
        float dist = length(uv - vec2(0.5, 0.7));
        float glow = exp(-dist * 2.8) * 0.8;

        // Accent orange tint #EA580C
        vec3 col = vec3(0.99, 0.99, 0.99); // clean white ground
        vec3 gridCol = vec3(0.92, 0.92, 0.92);
        vec3 orangeAccent = vec3(0.917, 0.345, 0.047); // #EA580C

        col = mix(col, gridCol, gridLine * 0.35);
        col = mix(col, orangeAccent, glow * 0.06 * (0.8 + 0.2 * pulse));

        gl_FragColor = vec4(col, 1.0);
      }
    `

    function createShader(gl, type, source) {
      const shader = gl.createShader(type)
      gl.shaderSource(shader, source)
      gl.compileShader(shader)
      return shader
    }

    const vs = createShader(gl, gl.VERTEX_SHADER, vsrc)
    const fs = createShader(gl, gl.FRAGMENT_SHADER, fsrc)
    const program = gl.createProgram()
    gl.attachShader(program, vs)
    gl.attachShader(program, fs)
    gl.linkProgram(program)
    gl.useProgram(program)

    // Full screen quad
    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW
    )

    const posLoc = gl.getAttribLocation(program, 'position')
    gl.enableVertexAttribArray(posLoc)
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0)

    const resLoc = gl.getUniformLocation(program, 'u_res')
    const timeLoc = gl.getUniformLocation(program, 'u_time')
    const mouseLoc = gl.getUniformLocation(program, 'u_mouse')

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const width = canvas.parentElement ? canvas.parentElement.clientWidth : window.innerWidth
      const height = canvas.parentElement ? canvas.parentElement.clientHeight : window.innerHeight
      canvas.width = width * dpr
      canvas.height = height * dpr
      gl.viewport(0, 0, canvas.width, canvas.height)
    }

    window.addEventListener('resize', resize)
    resize()

    const render = () => {
      const elapsed = (Date.now() - startTime) / 1000.0
      gl.uniform2f(resLoc, canvas.width, canvas.height)
      gl.uniform1f(timeLoc, elapsed)
      gl.uniform2f(mouseLoc, mouseX, mouseY)
      gl.drawArrays(gl.TRIANGLES, 0, 6)
      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity: 0.95 }}
    />
  )
}
