if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
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

    function makeBat() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        const fromLeft = Math.random() < 0.5;
        return {
            x: fromLeft ? -40 : width + 40,
            y: height * 0.1 + Math.random() * height * 0.6,
            heading: fromLeft ? 0 : Math.PI,
            speed: 25 + Math.random() * 20,
            turn: 0.5 + Math.random() * 0.5,
            wobble: Math.random() * Math.PI * 2,
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
            size: 13 + Math.random() * 12,
            alpha: 0.22 + Math.random() * 0.2,
        };
    }

    let bats = [];
    let running = false;
    let last = 0;

    function startFlyby() {
        bats.push(makeBat());
        if (Math.random() < 0.15) {
            bats.push(makeBat());
        }
        if (!running) {
            running = true;
            last = performance.now();
            requestAnimationFrame(frame);
        }
    }

    function scheduleNext(delay) {
        setTimeout(startFlyby, delay);
    }

    function frame(now) {
        const elapsed = Math.min((now - last) / 1000, 0.1);
        last = now;
        const width = window.innerWidth;
        const height = window.innerHeight;
        ctx.clearRect(0, 0, width, height);
        bats = bats.filter((bat) => {
            const target = bat.waypoints[0];
            const dx = target.x - bat.x;
            const dy = target.y - bat.y;
            if (Math.hypot(dx, dy) < 40) {
                bat.waypoints.shift();
            } else {
                const desired = Math.atan2(dy, dx);
                const diff = ((desired - bat.heading + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
                const step = Math.max(-bat.turn * elapsed, Math.min(bat.turn * elapsed, diff));
                bat.heading += step;
            }
            bat.wobble += elapsed * 0.7;
            bat.heading += Math.sin(bat.wobble) * 0.15 * elapsed;
            bat.x += Math.cos(bat.heading) * bat.speed * elapsed;
            bat.y += Math.sin(bat.heading) * bat.speed * elapsed;
            const inside = Math.min(bat.x, width - bat.x, bat.y, height - bat.y);
            if (inside < -100) {
                return false;
            }
            const fade = Math.max(0, Math.min(1, inside / 90));
            ctx.globalAlpha = bat.alpha * fade;
            ctx.font = `${bat.size}px serif`;
            ctx.fillText("🦇", bat.x, bat.y);
            return true;
        });
        ctx.globalAlpha = 1;
        if (bats.length > 0) {
            requestAnimationFrame(frame);
        } else {
            running = false;
            scheduleNext(10000 + Math.random() * 10000);
        }
    }

    scheduleNext(3000 + Math.random() * 5000);
}
