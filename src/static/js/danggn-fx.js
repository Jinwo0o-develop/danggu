/**
 * danggn-fx.js — SELL IT 공유 프론트엔드 이펙트 모듈
 *
 * 패턴:
 *   - Module Pattern: IIFE로 전역 오염 방지, DanggnFX 단일 네임스페이스 노출
 *   - Factory Function: createBgCanvas()가 독립 애니메이션 컨텍스트를 생성
 *   - Singleton-like: initCursor()는 중복 등록 방지
 *
 * 사용법:
 *   DanggnFX.initCursor();
 *   DanggnFX.createBgCanvas(document.getElementById('bgCanvas'));
 *   DanggnFX.createBgCanvas(sectionCanvas, { fullscreen: false, orbCount: 7 });
 */
const DanggnFX = (() => {
  'use strict';

  let _cursorInitialized = false;

  // ─────────────────────────────────────────────────────────
  // 커스텀 커서
  // ─────────────────────────────────────────────────────────

  function initCursor() {
    if (_cursorInitialized) return;
    _cursorInitialized = true;

    const cursor   = document.getElementById('cursor');
    const follower = document.getElementById('follower');
    if (!cursor || !follower) return;

    let mx = 0, my = 0, fx = 0, fy = 0;

    document.addEventListener('mousemove', e => {
      mx = e.clientX; my = e.clientY;
      cursor.style.left = mx - 6 + 'px';
      cursor.style.top  = my - 6 + 'px';
    });

    (function loop() {
      fx += (mx - fx - 18) * 0.12;
      fy += (my - fy - 18) * 0.12;
      follower.style.left = fx + 'px';
      follower.style.top  = fy + 'px';
      requestAnimationFrame(loop);
    })();
  }

  // ─────────────────────────────────────────────────────────
  // 배경 Canvas 애니메이션 팩토리
  //
  // options:
  //   fullscreen {boolean} — true: window 크기(기본값), false: 부모 엘리먼트 크기
  //   orbCount   {number}  — bokeh orb 개수 (기본값 8)
  //   emberCount {number}  — ember 파티클 개수 (기본값 75)
  // ─────────────────────────────────────────────────────────

  function createBgCanvas(canvas, options = {}) {
    if (!canvas) return;

    const ctx         = canvas.getContext('2d');
    const fullscreen  = options.fullscreen !== false;
    const orbCount    = options.orbCount   ?? 8;
    const emberCount  = options.emberCount ?? 75;

    // ── 크기 동기화 ──────────────────────────────────────
    function resize() {
      if (fullscreen) {
        canvas.width  = window.innerWidth;
        canvas.height = window.innerHeight;
      } else {
        canvas.width  = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
      }
    }
    resize();
    if (fullscreen) window.addEventListener('resize', resize);

    const W = () => canvas.width;
    const H = () => canvas.height;

    // ── Bokeh Orbs ───────────────────────────────────────
    const orbs = Array.from({ length: orbCount }, () => ({
      x:      Math.random() * W(),
      y:      Math.random() * H(),
      vx:     (Math.random() - 0.5) * 0.38,
      vy:     (Math.random() - 0.5) * 0.38,
      r:      160 + Math.random() * 220,
      phase:  Math.random() * Math.PI * 2,
      speed:  0.003 + Math.random() * 0.004,
      orange: Math.random() > 0.45,
    }));

    // ── Ember 파티클 팩토리 ──────────────────────────────
    function newEmber(fromBottom = true) {
      return {
        x:      Math.random() * W(),
        y:      fromBottom ? H() + 8 : Math.random() * H(),
        vx:     (Math.random() - 0.5) * 0.45,
        vy:     -(0.35 + Math.random() * 0.85),
        r:      0.7  + Math.random() * 1.9,
        alpha:  0.07 + Math.random() * 0.38,
        wobble: Math.random() * Math.PI * 2,
        ws:     0.018 + Math.random() * 0.032,
        orange: Math.random() > 0.5,
      };
    }
    const embers = Array.from({ length: emberCount }, () => newEmber(false));

    // ── 렌더 루프 ────────────────────────────────────────
    (function bgLoop() {
      ctx.clearRect(0, 0, W(), H());

      // Orbs
      orbs.forEach(o => {
        o.x += o.vx; o.y += o.vy; o.phase += o.speed;
        if (o.x < -o.r)       o.x = W() + o.r;
        if (o.x > W() + o.r)  o.x = -o.r;
        if (o.y < -o.r)       o.y = H() + o.r;
        if (o.y > H() + o.r)  o.y = -o.r;

        const a = 0.032 + Math.sin(o.phase) * 0.02;
        const g = ctx.createRadialGradient(o.x, o.y, 0, o.x, o.y, o.r);
        g.addColorStop(0, o.orange ? `rgba(242,100,25,${a})` : `rgba(134,187,216,${a})`);
        g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(o.x, o.y, o.r, 0, Math.PI * 2);
        ctx.fill();
      });

      // Embers
      embers.forEach(e => {
        e.wobble += e.ws;
        e.x += e.vx + Math.sin(e.wobble) * 0.28;
        e.y += e.vy;
        if (e.y < -8) Object.assign(e, newEmber(true));
        ctx.fillStyle = e.orange
          ? `rgba(242,100,25,${e.alpha})`
          : `rgba(134,187,216,${e.alpha})`;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
        ctx.fill();
      });

      requestAnimationFrame(bgLoop);
    })();
  }

  // ─────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────
  return { initCursor, createBgCanvas };

})();
