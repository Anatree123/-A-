import pygame, random, math

W, H = 960, 640
WY = H - 140             # 水面线
LT, LB = WY + 8, H - 12  # 落点上下限
RAIN_A_MIN, RAIN_A_MAX = 40, 200   # 雨滴透明度


# 摄像机
class Camera:
    """开场镜头对着雨地拍，随后远景。"""
    Z0, Z1 = 3.2, 1.0            # 起始 / 结束缩放
    HOLD, PULL = .8, 4.0         # 特写停留、拉远时长（秒）
    F0 = (W * .5, WY + 80.0)     # 起始注视点：直接压在水面上
    F1 = (W * .5, H * .5)        # 结束注视点：画面中心

    def __init__(self):
        self.t = -self.HOLD
        self.z = self.Z0
        self.fx, self.fy = self.F0

    def update(self, dt):
        self.t += dt
        if self.t <= 0:
            k = 0.0
        elif self.t >= self.PULL:
            k = 1.0
        else:
            k = self.t / self.PULL
            k = k * k * (3 - 2 * k)  # 平滑缓入缓出

        self.z = self.Z0 + (self.Z1 - self.Z0) * k
        self.fx = self.F0[0] + (self.F1[0] - self.F0[0]) * k
        self.fy = self.F0[1] + (self.F1[1] - self.F0[1]) * k

    def done(self):
        """镜头是否已经完全拉到全景"""
        return self.t >= self.PULL

    def pt(self, x, y):
        """世界坐标 -> 屏幕坐标"""
        return (
            (x - self.fx) * self.z + W * 0.5,
            (y - self.fy) * self.z + H * 0.5
        )


def bg_cols():
    cols = []
    for y in range(H):
        if y < WY - 14:
            t = y / (WY - 14)
            c = (int(120 - 35 * t), int(190 - 45 * t), int(250 - 25 * t))
        elif y < WY + 14:
            t = (y - WY + 14) / 28
            c = (int(85 - 45 * t), int(145 - 45 * t), int(225 - 25 * t))
        else:
            t = (y - WY - 14) / (H - WY - 14)
            c = (int(40 - 35 * t), int(100 - 85 * t), int(200 - 110 * t))
        cols.append(c)
    return cols


def petal(sz, col):     # 一朵花的底图
    sz = max(2, int(sz))
    s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
    for i in range(5):
        a = i * math.tau / 5 - math.pi / 2
        pygame.draw.circle(
            s,
            col,
            (sz + math.cos(a) * sz * 0.54, sz + math.sin(a) * sz * 0.54),
            sz * 0.46
        )
    pygame.draw.circle(s, (255, 250, 120), (sz, sz), max(1, int(sz * 0.3)))
    return s


class Drop:
    def __init__(self, first=False):
        d = random.random() ** 0.7
        self.sp = 400 + d * 900
        self.wind = 60 + d * 170
        self.depth = t = min(1, max(0, d + random.uniform(-0.22, 0.22)))
        r = int(150 + d * 90)
        g = int(210 + d * 45)
        a = int(RAIN_A_MIN + (RAIN_A_MAX - RAIN_A_MIN) * t)
        self.col = (r, g, 255, a)
        self.w = 1 if d < 0.45 else 2
        self.ly = LT + (LB - LT) * t
        self.x = random.uniform(-150, W + 150)
        self.y = random.uniform(0, self.ly) if first else random.uniform(-400, -10)
        k = (9 + d * 30) / math.hypot(self.wind, self.sp)
        self.dx, self.dy = -self.wind * k, -self.sp * k

    def step(self, dt):
        self.x += self.wind * dt
        self.y += self.sp * dt
        if self.y >= self.ly:
            hit = (self.x, self.ly, self.depth)   # 落点：x、水面高度、深度
            self.__init__()          # 落点到了，重开一颗
            return hit
        return None

    def draw(self, s, cam):
        x, y = cam.pt(self.x, self.y)
        if not (-80 <= x <= W + 80 and -80 <= y <= H + 80):
            return
        x2, y2 = cam.pt(self.x + self.dx, self.y + self.dy)
        pygame.draw.line(
            s,
            self.col,
            (x, y),
            (x2, y2),
            max(1, int(round(self.w * cam.z)))
        )


class Ripple:
    def __init__(self, x, y, depth, s=1):
        self.x, self.y, self.d = x, y, depth
        self.r = random.uniform(1.5, 3)
        self.maxr = (10 + 46 * depth) * s * random.uniform(0.85, 1.15)
        self.grow = (28 + 78 * depth) * s
        self.sq = 0.2 + 0.2 * depth
        self.ma = 30 + 70 * depth
        self.life = self.ml = 0.4 + 0.55 * depth
        self.w = 1 if depth < 0.65 else 2

    def step(self, dt):
        self.r += self.grow * dt
        self.life -= dt
        return self.life <= 0 or self.r >= self.maxr

    def draw(self, s, cam):
        a = int(self.ma * (self.life / self.ml) ** 1.5)
        z = cam.z
        w, h = int(self.r * 2 * z), int(self.r * 2 * self.sq * z)
        if a <= 3 or w < 2 or h < 1:
            return
        lw = max(1, int(round(self.w * z)))
        pad = lw + 2
        r = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(r, (140, 225, 255, a), (pad, pad, w, h), lw)
        x, y = cam.pt(self.x, self.y)
        s.blit(r, (int(x - r.get_width() // 2), int(y - r.get_height() // 2)))


PINK = [
    (255, 100, 180),
    (255, 145, 205),
    (255, 60, 155),
    (255, 180, 220),
    (255, 85, 170)
]


class Flower:
    def __init__(self, x, y, depth, s=1):
        self.x, self.y, self.d = x, y, depth
        sp = (0.65 + 0.55 * depth) * s
        a = random.uniform(math.pi * 1.18, math.pi * 1.82)
        v = random.uniform(280, 600) * sp
        self.vx, self.vy = math.cos(a) * v, math.sin(a) * v
        self.wa = random.uniform(-240, 240) * sp
        self.g = 520 * (0.85 + 0.15 * depth)
        self.size = random.randint(4, 7) + int(4 * depth)
        self.col = random.choice(PINK)
        self.ang = random.uniform(0, 360)
        self.spin = random.uniform(-220, 220) * (0.6 + 0.8 * depth)
        self.life = self.ml = random.uniform(3, 6) * (0.75 + 0.55 * depth)
        self.alpha = 0.72 + 0.28 * depth

    def step(self, dt):
        self.vy += self.g * dt
        self.vx += self.wa * dt
        self.vx *= 1 - 0.6 * dt
        self.vy *= 1 - 0.2 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.ang += self.spin * dt
        self.life -= dt
        m = 60
        return (
            self.life <= 0
            or self.x < -m
            or self.x > W + m
            or self.y > H + m
            or self.y < -m
        )

    def draw(self, s, cam):
        t = self.life / self.ml
        sz = self.size * cam.z
        img = pygame.transform.rotate(petal(sz, self.col), self.ang)
        a = self.alpha if t > 0.35 else self.alpha * t / 0.35
        img.set_alpha(int(255 * a))
        x, y = cam.pt(self.x, self.y)
        if not (-90 <= x <= W + 90 and -90 <= y <= H + 90):
            return
        s.blit(img, img.get_rect(center=(int(x), int(y))))


def main():
    pygame.init()
    sc = pygame.display.set_mode((W, H))
    pygame.display.set_caption("雨落生花  ESC 退出")
    clock = pygame.time.Clock()
    cols = bg_cols()
    cam = Camera()
    drops = [Drop(True) for _ in range(360)]
    ripples, flowers = [], []

    running = True
    while running:
        dt = min(clock.tick(60) / 1000, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN and e.key == 27:
                running = False

        cam.update(dt)

        # 背景：按镜头取样世界 y，逐行铺色
        z, fy = cam.z, cam.fy
        for sy in range(H):
            wy = int(fy + (sy - H * 0.5) / z)
            sc_y = 0 if wy < 0 else (H - 1 if wy >= H else wy)
            pygame.draw.line(sc, cols[sc_y], (0, sy), (W, sy))

        # 雨滴：落地时溅起涟漪，偶尔开出一朵花
        for d in drops:
            hit = d.step(dt)
            if hit:
                rx, ry, rd = hit
                ripples.append(Ripple(rx, ry, rd))
                if random.random() < 0.25:
                    flowers.append(Flower(rx, ry, rd))
            d.draw(sc, cam)

        # 涟漪：先推进，再绘制，消失的移除
        alive = []
        for r in ripples:
            if not r.step(dt):
                r.draw(sc, cam)
                alive.append(r)
        ripples = alive

        # 花瓣：同上
        alive = []
        for f in flowers:
            if not f.step(dt):
                f.draw(sc, cam)
                alive.append(f)
        flowers = alive

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()