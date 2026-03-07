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
 *   DanggnFX.createBgCanvas(lightCanvas, { colorScheme: 'light', orbCount: 4 });
 *   DanggnFX.autoInit();  // id="bgCanvas" + id="cursor" 자동 감지 초기화
 *
 * colorScheme 옵션:
 *   'dark'  (기본) — 어두운 배경용 오렌지/시안 파티클
 *   'light' — 밝은 배경용 저채도·저알파 파티클
 *   'warm'  — 오렌지 CTA 배경용 흰색/크림 파티클
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
    let firstMove = true;

    // 초기 숨김 — 첫 mousemove 전까지 표시하지 않음
    cursor.style.opacity   = '0';
    follower.style.opacity = '0';

    document.addEventListener('mousemove', e => {
      mx = e.clientX; my = e.clientY;
      cursor.style.left = mx - 6 + 'px';
      cursor.style.top  = my - 6 + 'px';

      if (firstMove) {
        // 새로고침 후 중앙에서 따라오지 않도록 첫 위치에서 바로 시작
        fx = mx - 18; fy = my - 18;
        firstMove = false;
      }

      cursor.style.opacity   = '';
      follower.style.opacity = '';
    });

    // 커서가 화면 밖으로 나가면 둘 다 숨김
    document.addEventListener('mouseleave', () => {
      cursor.style.opacity   = '0';
      follower.style.opacity = '0';
    });

    // 커서가 화면 안으로 돌아오면 다시 표시
    document.addEventListener('mouseenter', e => {
      if (!firstMove) {
        mx = e.clientX; my = e.clientY;
        cursor.style.left      = mx - 6 + 'px';
        cursor.style.top       = my - 6 + 'px';
        cursor.style.opacity   = '';
        follower.style.opacity = '';
      }
    });

    // 마지막 섹션(CTA, 오렌지 배경)에서 보색(파랑 #0D9BE6) 적용
    const ctaSection = document.getElementById('cta');
    if (ctaSection) {
      const ctaObs = new IntersectionObserver(entries => {
        const inCta = entries[0].isIntersecting;
        cursor.style.backgroundColor = inCta ? '#0D9BE6' : '';
        follower.style.borderColor   = inCta ? '#0D9BE6' : '';
      }, { threshold: 0.5 });
      ctaObs.observe(ctaSection);
    }

    (function loop() {
      // 0.12 → 0.25: 더 빠르게 따라오도록
      fx += (mx - fx - 18) * 0.25;
      fy += (my - fy - 18) * 0.25;
      follower.style.left = fx + 'px';
      follower.style.top  = fy + 'px';
      requestAnimationFrame(loop);
    })();
  }

  // ─────────────────────────────────────────────────────────
  // 배경 Canvas 애니메이션 팩토리
  //
  // options:
  //   fullscreen   {boolean} — true: window 크기(기본), false: 부모 엘리먼트 크기
  //   orbCount     {number}  — bokeh orb 개수 (기본 8)
  //   emberCount   {number}  — ember 파티클 개수 (기본 75)
  //   colorScheme  {string}  — 'dark'(기본) | 'light' | 'warm'
  // ─────────────────────────────────────────────────────────

  function createBgCanvas(canvas, options = {}) {
    if (!canvas) return;

    const ctx         = canvas.getContext('2d');
    const fullscreen  = options.fullscreen !== false;
    const orbCount    = options.orbCount   ?? 8;
    const emberCount  = options.emberCount ?? 75;
    const scheme      = options.colorScheme || 'dark';

    // ── 색상 헬퍼 ────────────────────────────────────────
    function orbColor(orange, alpha) {
      if (scheme === 'light') {
        return orange
          ? `rgba(200,70,5,${(alpha * 0.45).toFixed(3)})`
          : `rgba(60,130,190,${(alpha * 0.45).toFixed(3)})`;
      }
      if (scheme === 'warm') {
        return orange
          ? `rgba(255,255,255,${(alpha * 0.22).toFixed(3)})`
          : `rgba(255,220,170,${(alpha * 0.18).toFixed(3)})`;
      }
      return orange
        ? `rgba(242,100,25,${alpha})`
        : `rgba(134,187,216,${alpha})`;
    }

    function emberColor(orange, alpha) {
      if (scheme === 'light') {
        return orange
          ? `rgba(200,70,5,${(alpha * 0.35).toFixed(3)})`
          : `rgba(60,130,190,${(alpha * 0.35).toFixed(3)})`;
      }
      if (scheme === 'warm') {
        return `rgba(255,255,255,${(alpha * 0.30).toFixed(3)})`;
      }
      return orange
        ? `rgba(242,100,25,${alpha})`
        : `rgba(134,187,216,${alpha})`;
    }

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

    // ── 렌더 루프 (pause/resume 지원) ───────────────────
    let animId = null;

    function bgLoop() {
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
        g.addColorStop(0, orbColor(o.orange, a));
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
        ctx.fillStyle = emberColor(e.orange, e.alpha);
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.r, 0, Math.PI * 2);
        ctx.fill();
      });

      animId = requestAnimationFrame(bgLoop);
    }

    function startLoop() { if (animId === null) animId = requestAnimationFrame(bgLoop); }
    function stopLoop()  { cancelAnimationFrame(animId); animId = null; }

    startLoop();

    // 탭 숨김 시 루프 일시정지 → CPU/GPU 절약
    document.addEventListener('visibilitychange', () =>
      document.hidden ? stopLoop() : startLoop()
    );

    // 비전체화면 캔버스: 뷰포트 밖으로 나가면 일시정지
    if (!fullscreen) {
      new IntersectionObserver(
        ([entry]) => entry.isIntersecting ? startLoop() : stopLoop(),
        { threshold: 0 }
      ).observe(canvas);

      // 부모 크기 변화 감지 → 캔버스 크기 동기화
      new ResizeObserver(() => {
        canvas.width  = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
      }).observe(canvas.parentElement ?? canvas);
    }
  }

  // ─────────────────────────────────────────────────────────
  // autoInit — id="bgCanvas" + id="cursor" 자동 감지 초기화
  // ─────────────────────────────────────────────────────────

  function autoInit(options = {}) {
    const canvas = document.getElementById('bgCanvas');
    if (canvas) createBgCanvas(canvas, options);
    if (document.getElementById('cursor')) initCursor();
  }

  // ─────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────
  return { initCursor, createBgCanvas, autoInit };

})();
