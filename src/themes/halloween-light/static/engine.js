export function runSky(palette) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }
    const canvas = document.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    Object.assign(canvas.style, {
        position: "fixed",
        inset: "0",
        width: "100vw",
        height: "100vh",
        pointerEvents: "none",
        zIndex: "60",
    });
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");

    function resize() {
        const scale = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(window.innerWidth * scale);
        canvas.height = Math.floor(window.innerHeight * scale);
        ctx.setTransform(scale, 0, 0, scale, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    const KINDS = ["bat", "ghost"];

    function makeFlyer() {
        const kind = KINDS[Math.floor(Math.random() * KINDS.length)];
        const width = window.innerWidth;
        const height = window.innerHeight;
        const fromLeft = Math.random() < 0.5;
        const flyer = {
            kind,
            x: fromLeft ? -40 : width + 40,
            y: height * 0.1 + Math.random() * height * 0.6,
            heading: fromLeft ? 0 : Math.PI,
            wobble: Math.random() * Math.PI * 2,
            age: 0,
            entered: false,
            waypoints: [
                {
                    x: width * 0.2 + Math.random() * width * 0.6,
                    y: height * 0.15 + Math.random() * height * 0.55,
                },
                {
                    x: fromLeft ? width + 80 : -80,
                    y: Math.random() * height,
                },
            ],
        };
        if (kind === "ghost") {
            flyer.glyph = "👻";
            flyer.speed = 15 + Math.random() * 15;
            flyer.turn = 0.3 + Math.random() * 0.3;
            flyer.size = 18 + Math.random() * 12;
            flyer.alpha = palette.ghost[0] + Math.random() * palette.ghost[1];
        } else {
            flyer.glyph = "🦇";
            flyer.speed = 25 + Math.random() * 20;
            flyer.turn = 0.5 + Math.random() * 0.5;
            flyer.size = 13 + Math.random() * 12;
            flyer.alpha = palette.bat[0] + Math.random() * palette.bat[1];
        }
        return flyer;
    }

    function drawFlyer(flyer) {
        ctx.font = `${flyer.size}px serif`;
        ctx.fillText(flyer.glyph, flyer.x, flyer.y);
    }

    let flyers = [];
    let running = false;
    let last = 0;

    function startFlyby() {
        flyers.push(makeFlyer());
        if (Math.random() < 0.15) {
            flyers.push(makeFlyer());
        }
        if (!running) {
            running = true;
            last = performance.now();
            requestAnimationFrame(frame);
        }
    }

    function frame(now) {
        const elapsed = Math.min((now - last) / 1000, 0.1);
        last = now;
        const width = window.innerWidth;
        const height = window.innerHeight;
        ctx.clearRect(0, 0, width, height);
        flyers = flyers.filter((flyer) => {
            const target = flyer.waypoints[0];
            const dx = target.x - flyer.x;
            const dy = target.y - flyer.y;
            if (Math.hypot(dx, dy) < 40) {
                flyer.waypoints.shift();
            } else {
                const desired = Math.atan2(dy, dx);
                const diff = ((desired - flyer.heading + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
                const step = Math.max(-flyer.turn * elapsed, Math.min(flyer.turn * elapsed, diff));
                flyer.heading += step;
            }
            flyer.wobble += elapsed * 0.7;
            flyer.heading += Math.sin(flyer.wobble) * 0.15 * elapsed;
            flyer.x += Math.cos(flyer.heading) * flyer.speed * elapsed;
            flyer.y += Math.sin(flyer.heading) * flyer.speed * elapsed;
            flyer.age += elapsed;
            const inside = Math.min(flyer.x, width - flyer.x, flyer.y, height - flyer.y);
            if (inside >= 0) {
                flyer.entered = true;
            }
            ctx.font = `${flyer.size}px serif`;
            const glyphWidth = ctx.measureText(flyer.glyph).width;
            const exited = flyer.x < -glyphWidth || flyer.x > width
                || flyer.y < 0 || flyer.y > height + flyer.size;
            if (flyer.entered && exited) {
                return false;
            }
            ctx.globalAlpha = flyer.alpha * Math.min(1, flyer.age / 1.5);
            drawFlyer(flyer);
            return true;
        });
        ctx.globalAlpha = 1;
        if (flyers.length === 0) {
            flyers.push(makeFlyer());
            if (Math.random() < 0.15) {
                flyers.push(makeFlyer());
            }
        }
        requestAnimationFrame(frame);
    }

    startFlyby();
}
