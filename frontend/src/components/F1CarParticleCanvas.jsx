import React, { useRef, useEffect } from 'react';

const F1CarParticleCanvas = ({ compound = 'SOFT' }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    // Set canvas dimensions
    const handleResize = () => {
      canvas.width = canvas.parentElement.clientWidth;
      canvas.height = canvas.parentElement.clientHeight;
    };
    handleResize();
    window.addEventListener('resize', handleResize);

    const width = canvas.width;
    const height = canvas.height;

    // Compound color lookup
    const getCompoundColor = (comp) => {
      switch (comp.toUpperCase()) {
        case 'SOFT': return { primary: '#FF1801', secondary: '#FF5743' };
        case 'MEDIUM': return { primary: '#FFD700', secondary: '#FFE45E' };
        case 'HARD': return { primary: '#FFFFFF', secondary: '#A0B0C0' };
        default: return { primary: '#00F0FF', secondary: '#80F8FF' };
      }
    };

    const color = getCompoundColor(compound);

    // Generate F1 Car target shape points
    const generateF1CarShapePoints = (numPoints, cx, cy, scale) => {
      const points = [];
      
      // Nose cone & Front Wing
      for (let i = 0; i < 40; i++) {
        const t = i / 40;
        points.push({ x: cx - scale * (180 - t * 60), y: cy + (t - 0.5) * scale * 25 });
        points.push({ x: cx - scale * 180, y: cy + (t - 0.5) * scale * 80 }); // Front wing main plane
      }
      
      // Cockpit & Halo
      for (let i = 0; i < 35; i++) {
        const angle = Math.PI * (i / 35);
        points.push({ x: cx - scale * 20 + Math.cos(angle) * scale * 35, y: cy - scale * 25 - Math.sin(angle) * scale * 20 });
      }

      // Sidepods & Bodywork
      for (let i = 0; i < 60; i++) {
        const t = (i / 60) * 2 - 1;
        points.push({ x: cx + t * scale * 80, y: cy - scale * 28 });
        points.push({ x: cx + t * scale * 80, y: cy + scale * 28 });
      }

      // Front Wheels
      for (let i = 0; i < 40; i++) {
        const angle = (i / 40) * Math.PI * 2;
        points.push({ x: cx - scale * 120 + Math.cos(angle) * scale * 28, y: cy - scale * 45 + Math.sin(angle) * scale * 28 });
        points.push({ x: cx - scale * 120 + Math.cos(angle) * scale * 28, y: cy + scale * 45 + Math.sin(angle) * scale * 28 });
      }

      // Rear Wheels
      for (let i = 0; i < 50; i++) {
        const angle = (i / 50) * Math.PI * 2;
        points.push({ x: cx + scale * 100 + Math.cos(angle) * scale * 34, y: cy - scale * 48 + Math.sin(angle) * scale * 34 });
        points.push({ x: cx + scale * 100 + Math.cos(angle) * scale * 34, y: cy + scale * 48 + Math.sin(angle) * scale * 34 });
      }

      // Rear Wing
      for (let i = 0; i < 35; i++) {
        const t = i / 35;
        points.push({ x: cx + scale * (140 + t * 30), y: cy - scale * (40 - t * 5) });
        points.push({ x: cx + scale * (140 + t * 30), y: cy + scale * (40 - t * 5) });
        points.push({ x: cx + scale * 165, y: cy + (t - 0.5) * scale * 75 });
      }

      return points;
    };

    const cx = width / 2 + 40;
    const cy = height / 2 + 10;
    const scale = Math.min(width, height) / 420;

    const targetPoints = generateF1CarShapePoints(350, cx, cy, scale);
    const numParticles = 380;
    const particles = [];

    for (let i = 0; i < numParticles; i++) {
      const target = targetPoints[i % targetPoints.length];
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        tx: target.x + (Math.random() - 0.5) * 6,
        ty: target.y + (Math.random() - 0.5) * 6,
        vx: (Math.random() - 0.5) * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        size: Math.random() * 2.2 + 1.2,
        alpha: Math.random() * 0.7 + 0.3,
        pulseSpeed: Math.random() * 0.05 + 0.02,
        streamLine: Math.random() < 0.25 // 25% aerodynamic flow particles
      });
    }

    let mouseX = -1000;
    let mouseY = -1000;

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    };

    canvas.addEventListener('mousemove', handleMouseMove);

    // Animation Loop
    let time = 0;
    const render = () => {
      time += 0.02;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw subtle telemetry grid background
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw aerostream lines behind car
      ctx.strokeStyle = color.primary;
      ctx.lineWidth = 0.5;
      ctx.globalAlpha = 0.15;
      for (let i = 0; i < 5; i++) {
        const lineY = cy - 35 + i * 18;
        ctx.beginPath();
        ctx.moveTo(cx - 220, lineY + Math.sin(time + i) * 6);
        ctx.bezierCurveTo(
          cx - 80, lineY - 12,
          cx + 60, lineY + 12,
          cx + 220, lineY + Math.cos(time + i) * 10
        );
        ctx.stroke();
      }
      ctx.globalAlpha = 1.0;

      // Update and render dot particles
      particles.forEach((p) => {
        if (p.streamLine) {
          // Flow horizontally across screen like aerodynamic tunnel
          p.x += 4.5 + scale * 2;
          p.y += Math.sin(time * 2 + p.x * 0.01) * 0.8;
          if (p.x > canvas.width + 20) {
            p.x = -20;
            p.y = cy + (Math.random() - 0.5) * 140;
          }
        } else {
          // Spring toward target F1 shape point
          const dx = p.tx - p.x;
          const dy = p.ty - p.y;
          p.vx += dx * 0.008;
          p.vy += dy * 0.008;
          p.vx *= 0.90;
          p.vy *= 0.90;

          // Mouse repulsion force
          const mdx = p.x - mouseX;
          const mdy = p.y - mouseY;
          const dist = Math.sqrt(mdx * mdx + mdy * mdy);
          if (dist < 70) {
            const force = (70 - dist) / 70;
            p.vx += (mdx / dist) * force * 4.0;
            p.vy += (mdy / dist) * force * 4.0;
          }

          p.x += p.vx;
          p.y += p.vy;
        }

        // Draw particle dot with glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.streamLine ? '#00F0FF' : color.primary;
        ctx.shadowBlur = 10;
        ctx.shadowColor = p.streamLine ? '#00F0FF' : color.primary;
        ctx.globalAlpha = p.alpha * (0.8 + Math.sin(time * 3 + p.x) * 0.2);
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, [compound]);

  return (
    <div className="f1-particle-hero">
      <div className="canvas-overlay-text">
        <div className="canvas-title">F1 Telemetry Dot Matrix — RB20 Contour</div>
        <div className="canvas-subtitle">Real-time particle aerostream • Compound: {compound}</div>
      </div>
      <canvas ref={canvasRef} />
    </div>
  );
};

export default F1CarParticleCanvas;
