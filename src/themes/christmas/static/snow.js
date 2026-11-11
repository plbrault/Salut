export function runSnow(palette) {
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
        zIndex: "-1",
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

    function makeFlake(anywhere) {
        const width = window.innerWidth;
        const height = window.innerHeight;
        return {
            x: Math.random() * width,
            y: anywhere ? Math.random() * height : -10 - Math.random() * 40,
            radius: 1.5 + Math.random() * 2.5,
            speed: 25 + Math.random() * 40,
            sway: Math.random() * Math.PI * 2,
            swaySpeed: 0.5 + Math.random() * 1.0,
            alpha: palette.alpha[0] + Math.random() * palette.alpha[1],
        };
    }

    const flakes = [];
    for (let i = 0; i < palette.count; i++) {
        flakes.push(makeFlake(true));
    }

    function frame(now) {
        const elapsed = Math.min((now - last) / 1000, 0.1);
        last = now;
        const width = window.innerWidth;
        const height = window.innerHeight;
        ctx.clearRect(0, 0, width, height);
        for (const flake of flakes) {
            flake.sway += flake.swaySpeed * elapsed;
            flake.y += flake.speed * elapsed;
            flake.x += Math.sin(flake.sway) * 12 * elapsed;
            if (flake.y > height + flake.radius) {
                Object.assign(flake, makeFlake(false));
            }
            if (flake.x < -flake.radius) {
                flake.x = width + flake.radius;
            } else if (flake.x > width + flake.radius) {
                flake.x = -flake.radius;
            }
            ctx.globalAlpha = flake.alpha;
            ctx.beginPath();
            ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgb(${palette.color.join(", ")})`;
            ctx.fill();
        }
        ctx.globalAlpha = 1;
        requestAnimationFrame(frame);
    }

    let last = 0;
    requestAnimationFrame(frame);
}
