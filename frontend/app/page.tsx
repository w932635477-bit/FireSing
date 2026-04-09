import Link from "next/link";
import LazyBelowFold from "./home/lazy-below-fold";

export default function LandingPage() {
  return (
    <div className="bg-surface-container-lowest text-on-surface">
      {/* Top Navigation */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="text-2xl font-black text-ember tracking-tight">FireSing</div>
        <nav className="hidden md:flex gap-8 items-center">
          <Link href="/" className="text-ember font-bold border-b-2 border-ember px-3 py-2">首页</Link>
          <Link href="/dashboard" prefetch={false} className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">我的作品</Link>
          <Link href="/pricing" className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">充值</Link>
        </nav>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            prefetch={false}
            className="bg-ember text-on-primary-fixed font-bold px-5 py-2 rounded shadow-[0_8px_32px_rgba(255,107,53,0.15)] active:scale-[0.98] transition-transform"
          >
            开始创作
          </Link>
          <Link href="/login" className="w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-white/10 flex items-center justify-center hover:bg-surface-variant hover:border-white/20 transition-all active:scale-[0.95]">
            <span className="material-symbols-outlined text-white/60">person</span>
          </Link>
        </div>
      </header>

      <main className="pt-0">
        {/* ===== HERO SECTION ===== */}
        <section className="relative min-h-screen overflow-hidden">
          <div className="absolute inset-0 z-0">
            <video
              autoPlay
              muted
              loop
              playsInline
              poster="/images/chorus-feature.webp"
              className="w-full h-full object-cover opacity-30"
            >
              <source src="/video/hero-bg.mp4" type="video/mp4" />
            </video>
            <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-black/30" />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/50" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,107,53,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,107,53,0.02)_1px,transparent_1px)] bg-[size:80px_80px]" />
          </div>

          <div className="absolute top-1/3 left-[10%] w-[500px] h-[500px] bg-ember/10 rounded-full blur-[180px] z-[1]" />

          <div className="relative z-10 min-h-screen flex items-center">
            <div className="w-full max-w-7xl mx-auto px-6 md:px-16 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              <div className="lg:col-span-7 pt-28 lg:pt-0">
                <h1 className="text-5xl sm:text-7xl md:text-8xl lg:text-[7rem] font-black tracking-tighter leading-[0.9] mb-8">
                  <span className="bg-gradient-to-b from-white via-white/90 to-white/30 bg-clip-text text-transparent">老歌</span>
                  <br />
                  <span className="text-ember">换个声音唱</span>
                </h1>
                <p className="text-lg md:text-xl text-on-surface-variant mb-12 max-w-lg leading-relaxed font-medium">
                  上传一首歌，选几种方言音色，两分钟拿到翻唱视频。抖音、快手直接发。
                </p>
                <div className="flex flex-col sm:flex-row gap-4 items-start">
                  <Link
                    href="/dashboard"
                    prefetch={false}
                    className="bg-ember text-on-primary-fixed font-black text-lg px-10 py-4 rounded-lg shadow-[0_8px_40px_rgba(255,107,53,0.4)] active:scale-[0.98] transition-all hover:shadow-[0_12px_60px_rgba(255,107,53,0.6)]"
                  >
                    开始创作
                  </Link>
                  <a href="#how-it-works" className="bg-white/5 backdrop-blur-md text-on-surface font-bold text-lg px-10 py-4 rounded-lg border border-white/10 hover:bg-white/10 active:scale-[0.98] transition-all flex items-center gap-2">
                    看看怎么用 <span className="material-symbols-outlined">play_circle</span>
                  </a>
                </div>

                <div className="flex gap-10 mt-14">
                  {[
                    { value: "3步", label: "完成创作" },
                    { value: "竖版", label: "适配短视频" },
                    { value: "<2min", label: "处理速度" },
                  ].map((stat) => (
                    <div key={stat.label}>
                      <div className="text-2xl md:text-3xl font-black text-ember font-mono">{stat.value}</div>
                      <div className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="lg:col-span-5 relative hidden lg:block">
                <div className="absolute -top-4 text-xs font-bold text-ember/60 uppercase tracking-widest mb-3">你能做什么</div>
                <div className="grid grid-cols-1 gap-4 pt-6">
                  {[
                    { title: "方言翻唱", desc: "用方言音色重新演绎经典老歌", icon: "mic" },
                    { title: "多人合唱", desc: "一首歌分配多种音色，自动合唱", icon: "group" },
                    { title: "竖版视频", desc: "自带动态歌词背景，直接发短视频", icon: "smartphone" },
                  ].map((item, i) => (
                    <div
                      key={i}
                      className="group relative rounded-xl overflow-hidden border border-white/5 hover:border-ember/20 transition-all duration-300 hover:shadow-[0_8px_24px_rgba(255,107,53,0.15)] cursor-pointer flex items-center gap-4 p-4"
                    >
                      <div className="w-14 h-14 rounded-lg bg-ember/10 flex items-center justify-center flex-shrink-0">
                        <span className="material-symbols-outlined text-ember text-2xl">{item.icon}</span>
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-white">{item.title}</p>
                        <p className="text-xs text-on-surface-variant truncate">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Audio Waveform */}
          <div className="absolute bottom-0 left-0 right-0 z-[2]">
            <div className="h-px bg-gradient-to-r from-transparent via-ember/30 to-transparent" />
            <div className="flex items-end justify-center gap-[2px] h-20 px-6 opacity-40">
              {[
                20, 35, 50, 40, 65, 30, 55, 70, 45, 80, 35, 60, 50, 75, 40, 55, 70, 45, 60, 35,
                55, 75, 50, 65, 40, 80, 55, 45, 70, 35, 60, 50, 75, 40, 55, 70, 45, 60, 35, 50,
                65, 30, 55, 70, 45, 80, 35, 60, 50, 75, 40, 55, 70, 45, 60, 35, 50, 40, 30, 20,
              ].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 max-w-[3px] bg-gradient-to-t from-ember/60 to-ember/10 rounded-full"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
          </div>

          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[3] flex flex-col items-center gap-2 opacity-40 animate-bounce">
            <span className="text-[10px] font-mono text-on-surface-variant uppercase tracking-widest">向下滚动</span>
            <span className="material-symbols-outlined text-sm text-ember">expand_more</span>
          </div>
        </section>

        {/* Below-fold content loaded lazily */}
        <LazyBelowFold />
      </main>
    </div>
  );
}
