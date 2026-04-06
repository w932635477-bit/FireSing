import Link from "next/link";
import Image from "next/image";

export default function LandingPage() {
  return (
    <div className="bg-surface-container-lowest text-on-surface">
      {/* Top Navigation */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="text-2xl font-black text-ember tracking-tight">FireSing</div>
        <nav className="hidden md:flex gap-8 items-center">
          <Link href="/" className="text-ember font-bold border-b-2 border-ember px-3 py-2">首页</Link>
          <Link href="/dashboard" prefetch={false} className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">工作台</Link>
          <Link href="/dashboard" prefetch={false} className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">曲库</Link>
          <span className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors cursor-pointer">会员方案</span>
        </nav>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            prefetch={false}
            className="bg-ember text-on-primary-fixed font-bold px-5 py-2 rounded shadow-[0_8px_32px_rgba(255,107,53,0.15)] active:scale-[0.98] transition-transform"
          >
            上传新歌
          </Link>
          <Link href="/login" className="w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-white/10 flex items-center justify-center hover:bg-surface-variant hover:border-white/20 transition-all active:scale-[0.95]">
            <span className="material-symbols-outlined text-white/60">person</span>
          </Link>
        </div>
      </header>

      <main className="pt-0">
        {/* ===== HERO SECTION - Redesigned ===== */}
        <section className="relative min-h-screen overflow-hidden">
          {/* Background Video Layer */}
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
            {/* Dark overlay with gradient */}
            <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-black/30" />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/50" />
            {/* Grid texture */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,107,53,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,107,53,0.02)_1px,transparent_1px)] bg-[size:80px_80px]" />
          </div>

          {/* Ember glow behind text */}
          <div className="absolute top-1/3 left-[10%] w-[500px] h-[500px] bg-ember/10 rounded-full blur-[180px] z-[1]" />

          {/* Main Hero Content - Asymmetric Left-Aligned */}
          <div className="relative z-10 min-h-screen flex items-center">
            <div className="w-full max-w-7xl mx-auto px-6 md:px-16 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
              {/* Left: Text Content (7 cols) */}
              <div className="lg:col-span-7 pt-28 lg:pt-0">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-ember/10 border border-ember/20 text-ember text-xs font-bold uppercase tracking-widest mb-10">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-ember opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-ember" />
                  </span>
                  全新 AI 引擎已上线
                </div>
                <h1 className="text-5xl sm:text-7xl md:text-8xl lg:text-[7rem] font-black tracking-tighter leading-[0.9] mb-8">
                  <span className="bg-gradient-to-b from-white via-white/90 to-white/30 bg-clip-text text-transparent">
                    一首歌
                  </span>
                  <br />
                  <span className="text-ember">十种声音</span>
                </h1>
                <p className="text-lg md:text-xl text-on-surface-variant mb-12 max-w-lg leading-relaxed font-medium">
                  AI 驱动的多人多音色翻唱平台。上传一首歌，分配不同 AI 音色，生成合唱作品和竖版视频。
                </p>
                <div className="flex flex-col sm:flex-row gap-4 items-start">
                  <Link
                    href="/dashboard"
                    prefetch={false}
                    className="bg-ember text-on-primary-fixed font-black text-lg px-10 py-4 rounded-lg shadow-[0_8px_40px_rgba(255,107,53,0.4)] active:scale-[0.98] transition-all hover:shadow-[0_12px_60px_rgba(255,107,53,0.6)]"
                  >
                    立即体验
                  </Link>
                  <a href="#how-it-works" className="bg-white/5 backdrop-blur-md text-on-surface font-bold text-lg px-10 py-4 rounded-lg border border-white/10 hover:bg-white/10 active:scale-[0.98] transition-all flex items-center gap-2">
                    查看演示 <span className="material-symbols-outlined">play_circle</span>
                  </a>
                </div>

                {/* Stats row */}
                <div className="flex gap-10 mt-14">
                  {[
                    { value: "10K+", label: "创作者" },
                    { value: "50K+", label: "作品" },
                    { value: "99.2%", label: "满意度" },
                  ].map((stat) => (
                    <div key={stat.label}>
                      <div className="text-2xl md:text-3xl font-black text-ember font-mono">{stat.value}</div>
                      <div className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right: Featured Works Grid (5 cols) */}
              <div className="lg:col-span-5 relative hidden lg:block">
                <div className="absolute -top-4 text-xs font-bold text-ember/60 uppercase tracking-widest mb-3">热门作品</div>
                <div className="grid grid-cols-2 gap-4 pt-6">
                  {[
                    { title: "稻香", artist: "周杰伦", voices: 3, status: "done", cover: "/images/cover-vinyl.webp" },
                    { title: "珊瑚海", artist: "周杰伦 / Lara", voices: 2, status: "processing", cover: "/images/cover-waves.webp" },
                    { title: "晴天", artist: "周杰伦", voices: 4, status: "done", cover: "/images/cover-headphones.webp" },
                    { title: "七里香", artist: "周杰伦", voices: 3, status: "done", cover: "/images/cover-piano.webp" },
                  ].map((song, i) => (
                    <div
                      key={i}
                      className="group relative rounded-xl overflow-hidden border border-white/5 hover:border-ember/20 transition-all duration-300 hover:shadow-[0_8px_24px_rgba(255,107,53,0.15)] cursor-pointer"
                    >
                      <div className="aspect-square relative">
                        <Image
                          src={song.cover}
                          alt={song.title}
                          fill
                          className="object-cover"
                          sizes="(max-width:300px) 50vw, 25vw"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                        {/* Status badge */}
                        <div className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-[9px] font-bold flex items-center gap-1 ${
                          song.status === "done" ? "bg-success/20 text-success" : "bg-ember/20 text-ember"
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${song.status === "done" ? "bg-success" : "bg-ember animate-pulse"}`} />
                          {song.status === "done" ? "完成" : "处理中"}
                        </div>
                        {/* Play button on hover */}
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                          <div className="w-10 h-10 rounded-full bg-ember flex items-center justify-center shadow-lg shadow-ember/30">
                            <span className="material-symbols-outlined text-white text-xl" style={{ fontVariationSettings: '"FILL" 1' }}>play_arrow</span>
                          </div>
                        </div>
                      </div>
                      <div className="p-3">
                        <p className="text-sm font-bold text-white truncate">{song.title}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-on-surface-variant truncate">{song.artist}</span>
                          <div className="flex items-center gap-1">
                            <span className="material-symbols-outlined text-ember text-[10px]">mic</span>
                            <span className="text-[9px] text-on-surface-variant font-mono">{song.voices} 声部</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Audio Waveform - spans full width */}
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

          {/* Scroll indicator */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[3] flex flex-col items-center gap-2 opacity-40 animate-bounce">
            <span className="text-[10px] font-mono text-on-surface-variant uppercase tracking-widest">向下滚动</span>
            <span className="material-symbols-outlined text-sm text-ember">expand_more</span>
          </div>
        </section>

        {/* Three-Step Guide - Redesigned */}
        <section className="relative py-32 px-6 overflow-hidden">
          {/* Section background atmosphere */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-1/4 w-[600px] h-[400px] bg-ember/3 rounded-full blur-[150px]" />
            <div className="absolute bottom-0 right-1/4 w-[500px] h-[300px] bg-secondary/3 rounded-full blur-[120px]" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[300px] bg-tertiary-dim/2 rounded-full blur-[200px]" />
          </div>

          <div id="how-it-works" className="max-w-7xl mx-auto relative z-10">
            <div className="text-center mb-20">
              <span className="text-ember font-bold text-sm uppercase tracking-[0.3em] font-mono mb-4 block">How it works</span>
              <h2 className="text-5xl md:text-6xl font-black tracking-tighter">三步完成创作</h2>
            </div>

            <div className="relative">
              {/* Flow connector line (desktop only) */}
              <div className="hidden md:block absolute top-1/2 left-0 right-0 h-px -translate-y-1/2 z-0">
                <div className="h-full bg-gradient-to-r from-ember/30 via-secondary/30 to-tertiary-dim/30" />
                {/* Flow dots */}
                <div className="absolute left-[33.3%] top-1/2 -translate-y-1/2 -translate-x-1/2">
                  <div className="w-3 h-3 rounded-full bg-secondary/40 animate-glow-pulse" />
                </div>
                <div className="absolute left-[66.6%] top-1/2 -translate-y-1/2 -translate-x-1/2">
                  <div className="w-3 h-3 rounded-full bg-tertiary-dim/40 animate-glow-pulse" style={{ animationDelay: "1.5s" }} />
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-8 relative z-10">
                {/* Step 01: Upload */}
                <div className="group relative">
                  {/* Outer glow */}
                  <div className="absolute -inset-1 bg-gradient-to-br from-ember/20 via-transparent to-ember/5 rounded-[40px] opacity-0 group-hover:opacity-100 transition-all duration-500 blur-sm" />
                  <div className="relative bg-surface-container rounded-[40px] overflow-hidden border border-white/5 group-hover:border-ember/20 transition-all duration-500">
                    {/* Background image */}
                    <Image
                      src="/images/step-upload.webp"
                      alt=""
                      fill
                      sizes="400px"
                      className="object-cover opacity-25 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700"
                    />
                    {/* Dark gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/40" />
                    {/* Ember tint */}
                    <div className="absolute inset-0 bg-ember/5 group-hover:bg-ember/10 transition-colors duration-500" />
                    {/* Grid pattern */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,107,53,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,107,53,0.02)_1px,transparent_1px)] bg-[size:40px_40px] opacity-30" />

                    <div className="relative z-10 p-10">
                      {/* Step number + Icon row */}
                      <div className="flex items-start justify-between mb-12">
                        <div className="relative">
                          {/* Icon glow halo */}
                          <div className="absolute inset-0 bg-ember/20 rounded-2xl blur-xl animate-glow-pulse" />
                          <div className="relative w-16 h-16 bg-gradient-to-br from-ember/20 to-ember/5 rounded-2xl flex items-center justify-center border border-ember/20">
                            <span className="material-symbols-outlined text-ember text-3xl">cloud_upload</span>
                          </div>
                        </div>
                        <span className="text-ember/20 font-black font-mono text-7xl leading-none select-none">01</span>
                      </div>

                      {/* Mini visual: upload animation */}
                      <div className="flex items-center gap-3 mb-6">
                        <div className="flex -space-x-2">
                          <div className="w-10 h-10 rounded-lg bg-ember/10 border border-ember/20 flex items-center justify-center">
                            <span className="material-symbols-outlined text-ember text-sm">audio_file</span>
                          </div>
                          <div className="w-10 h-10 rounded-lg bg-ember/10 border border-ember/20 flex items-center justify-center">
                            <span className="material-symbols-outlined text-ember text-sm">description</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-ember text-lg animate-bounce" style={{ animationDelay: "0.3s" }}>arrow_downward</span>
                        </div>
                        <div className="w-10 h-10 rounded-lg bg-ember/20 border border-ember/30 flex items-center justify-center">
                          <span className="material-symbols-outlined text-ember text-sm" style={{ fontVariationSettings: '"FILL" 1' }}>cloud_done</span>
                        </div>
                      </div>

                      <h3 className="text-3xl font-black mb-3 text-white tracking-tight">上传</h3>
                      <p className="text-on-surface-variant text-base font-medium leading-relaxed">拖拽上传音频文件与 LRC 歌词，支持 MP3、WAV、FLAC 格式。</p>
                    </div>
                  </div>
                </div>

                {/* Step 02: Assign */}
                <div className="group relative md:mt-8">
                  {/* Outer glow */}
                  <div className="absolute -inset-1 bg-gradient-to-br from-secondary/20 via-transparent to-secondary/5 rounded-[40px] opacity-0 group-hover:opacity-100 transition-all duration-500 blur-sm" />
                  <div className="relative bg-surface-container rounded-[40px] overflow-hidden border border-white/5 group-hover:border-secondary/20 transition-all duration-500">
                    {/* Background image */}
                    <Image
                      src="/images/step-assign.webp"
                      alt=""
                      fill
                      sizes="400px"
                      className="object-cover opacity-25 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700"
                    />
                    {/* Dark gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/40" />
                    {/* Blue tint */}
                    <div className="absolute inset-0 bg-secondary/5 group-hover:bg-secondary/10 transition-colors duration-500" />
                    {/* Grid pattern */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(95,158,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(95,158,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] opacity-30" />

                    <div className="relative z-10 p-10">
                      <div className="flex items-start justify-between mb-12">
                        <div className="relative">
                          <div className="absolute inset-0 bg-secondary/20 rounded-2xl blur-xl animate-glow-pulse" style={{ animationDelay: "1s" }} />
                          <div className="relative w-16 h-16 bg-gradient-to-br from-secondary/20 to-secondary/5 rounded-2xl flex items-center justify-center border border-secondary/20">
                            <span className="material-symbols-outlined text-secondary text-3xl">auto_awesome</span>
                          </div>
                        </div>
                        <span className="text-secondary/20 font-black font-mono text-7xl leading-none select-none">02</span>
                      </div>

                      {/* Mini visual: voice assignment */}
                      <div className="flex items-center gap-2 mb-6">
                        <div className="flex gap-1.5">
                          <div className="w-7 h-7 rounded-full bg-ember/30 border border-ember/30 flex items-center justify-center">
                            <span className="text-[8px] font-mono text-ember font-bold">A</span>
                          </div>
                          <div className="w-7 h-7 rounded-full bg-secondary/30 border border-secondary/30 flex items-center justify-center">
                            <span className="text-[8px] font-mono text-secondary font-bold">B</span>
                          </div>
                          <div className="w-7 h-7 rounded-full bg-success/30 border border-success/30 flex items-center justify-center">
                            <span className="text-[8px] font-mono text-success font-bold">C</span>
                          </div>
                        </div>
                        <span className="material-symbols-outlined text-secondary text-sm">shuffle</span>
                        <div className="flex-1 h-6 bg-surface-container-highest rounded-full overflow-hidden p-[1px]">
                          <div className="bg-gradient-to-r from-secondary/40 to-secondary/80 h-full w-3/4 rounded-full" />
                        </div>
                      </div>

                      <h3 className="text-3xl font-black mb-3 text-white tracking-tight">分配</h3>
                      <p className="text-on-surface-variant text-base font-medium leading-relaxed">AI 自动为每段歌词分配不同音色，或手动选择你喜欢的声音。</p>
                    </div>
                  </div>
                </div>

                {/* Step 03: Generate */}
                <div className="group relative md:mt-4">
                  {/* Outer glow */}
                  <div className="absolute -inset-1 bg-gradient-to-br from-tertiary-dim/20 via-transparent to-tertiary-dim/5 rounded-[40px] opacity-0 group-hover:opacity-100 transition-all duration-500 blur-sm" />
                  <div className="relative bg-surface-container rounded-[40px] overflow-hidden border border-white/5 group-hover:border-tertiary-dim/20 transition-all duration-500">
                    {/* Background image */}
                    <Image
                      src="/images/step-generate.webp"
                      alt=""
                      fill
                      sizes="400px"
                      className="object-cover opacity-25 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700"
                    />
                    {/* Dark gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/40" />
                    {/* Green tint */}
                    <div className="absolute inset-0 bg-tertiary-dim/5 group-hover:bg-tertiary-dim/10 transition-colors duration-500" />
                    {/* Grid pattern */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(84,238,112,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(84,238,112,0.02)_1px,transparent_1px)] bg-[size:40px_40px] opacity-30" />

                    <div className="relative z-10 p-10">
                      <div className="flex items-start justify-between mb-12">
                        <div className="relative">
                          <div className="absolute inset-0 bg-tertiary-dim/20 rounded-2xl blur-xl animate-glow-pulse" style={{ animationDelay: "2s" }} />
                          <div className="relative w-16 h-16 bg-gradient-to-br from-tertiary-dim/20 to-tertiary-dim/5 rounded-2xl flex items-center justify-center border border-tertiary-dim/20">
                            <span className="material-symbols-outlined text-tertiary-dim text-3xl">movie</span>
                          </div>
                        </div>
                        <span className="text-tertiary-dim/20 font-black font-mono text-7xl leading-none select-none">03</span>
                      </div>

                      {/* Mini visual: video generation */}
                      <div className="flex items-center gap-2 mb-6">
                        <div className="w-14 h-9 rounded-md bg-tertiary-dim/10 border border-tertiary-dim/20 flex items-center justify-center relative overflow-hidden">
                          <span className="material-symbols-outlined text-tertiary-dim text-sm" style={{ fontVariationSettings: '"FILL" 1' }}>play_arrow</span>
                          <div className="absolute bottom-0 left-0 right-0 h-1 bg-tertiary-dim/30">
                            <div className="h-full w-2/3 bg-tertiary-dim rounded-r-full" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-mono text-tertiary-dim font-bold">1080P</span>
                          <span className="text-[9px] font-mono text-on-surface-variant">竖版 9:16</span>
                        </div>
                        <span className="material-symbols-outlined text-tertiary-dim text-sm ml-auto">download</span>
                      </div>

                      <h3 className="text-3xl font-black mb-3 text-white tracking-tight">生成</h3>
                      <p className="text-on-surface-variant text-base font-medium leading-relaxed">一键生成竖版音乐视频，适配抖音、Shorts 等平台，自带动态歌词。</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Grid (Bento) - with real AI images */}
        <section className="py-32 px-6 bg-surface-container-low/50">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 auto-rows-[280px]">
              {/* Large Feature - Multi-voice Chorus */}
              <div className="md:col-span-8 md:row-span-2 bg-surface-container rounded-[40px] overflow-hidden relative border border-white/5 group">
                <Image
                  src="/images/chorus-feature.webp"
                  alt="AI 多人合唱模式"
                  fill
                  sizes="(max-width: 768px) 100vw, 66vw"
                  className="object-cover opacity-40 group-hover:opacity-50 group-hover:scale-105 transition-all duration-700"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
                <div className="relative z-10 h-full flex flex-col justify-end p-12">
                  <span className="text-ember font-black text-sm uppercase tracking-[0.2em] mb-4 block">专业级表现</span>
                  <h3 className="text-4xl md:text-5xl font-black mb-4 leading-tight">
                    多人合唱模式<br />
                    <span className="text-ember">Multi-voice chorus</span>
                  </h3>
                  <p className="text-on-surface-variant text-lg max-w-md font-medium leading-relaxed">
                    突破单人翻唱限制，为每个段落分配专属音色，打造属于你的虚拟乐团。
                  </p>
                </div>
              </div>

              {/* Vertical Video */}
              <div className="md:col-span-4 md:row-span-2 bg-surface-container rounded-[40px] overflow-hidden relative border border-white/5">
                <Image
                  src="/images/vertical-video-feature.webp"
                  alt="竖版视频生成"
                  fill
                  sizes="(max-width: 768px) 100vw, 33vw"
                  className="object-cover opacity-30"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent" />
                <div className="relative z-10 h-full flex flex-col justify-between p-10">
                  <div>
                    <h3 className="text-2xl font-black mb-3 tracking-tight">竖版视频生成</h3>
                    <p className="text-on-surface-variant text-sm font-medium">
                      适配抖音/Shorts的竖版音乐视频，自带动态歌词效果。
                    </p>
                  </div>
                  <div className="flex items-center gap-3 mt-auto">
                    <span className="material-symbols-outlined text-ember text-3xl">play_circle</span>
                    <span className="text-ember font-bold text-sm">查看示例</span>
                  </div>
                </div>
              </div>

              {/* Monologue */}
              <div className="md:col-span-6 bg-surface-container rounded-[40px] overflow-hidden relative border border-white/5 hover:bg-surface-bright transition-colors group">
                <Image
                  src="/images/monologue-feature.webp"
                  alt="个性化独白"
                  fill
                  sizes="(max-width: 768px) 100vw, 50vw"
                  className="object-cover opacity-20 group-hover:opacity-30 transition-opacity duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-black/80 to-transparent" />
                <div className="relative z-10 h-full flex items-center gap-8 p-10">
                  <div className="w-20 h-20 bg-secondary/20 rounded-2xl flex-shrink-0 flex items-center justify-center border border-secondary/20 backdrop-blur-sm">
                    <span className="material-symbols-outlined text-secondary text-4xl">record_voice_over</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-black mb-3">个性化独白</h3>
                    <p className="text-on-surface-variant text-base font-medium">插入个性化独白，让作品更具情感深度。</p>
                  </div>
                </div>
              </div>

              {/* Preservation */}
              <div className="md:col-span-6 bg-surface-container rounded-[40px] overflow-hidden relative border border-white/5 hover:bg-surface-bright transition-colors group">
                <Image
                  src="/images/preservation-feature.webp"
                  alt="原声细节保留"
                  fill
                  sizes="(max-width: 768px) 100vw, 50vw"
                  className="object-cover opacity-20 group-hover:opacity-30 transition-opacity duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-black/80 to-transparent" />
                <div className="relative z-10 h-full flex items-center gap-8 p-10">
                  <div className="w-20 h-20 bg-tertiary/20 rounded-2xl flex-shrink-0 flex items-center justify-center border border-tertiary/20 backdrop-blur-sm">
                    <span className="material-symbols-outlined text-tertiary text-4xl">settings_input_component</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-black mb-3">原声细节保留</h3>
                    <p className="text-on-surface-variant text-base font-medium">完美保留原曲混响与动态，高保真还原音质。</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section className="py-32 px-6 bg-surface-container-low/30" id="pricing">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-20">
              <h2 className="text-5xl md:text-6xl font-black tracking-tighter mb-8">选择适合你的方案</h2>
              <p className="text-on-surface-variant text-xl max-w-2xl mx-auto font-medium">
                释放你的创意潜力。从基础创作到专业音频工程，我们为你量身打造了多款灵活的方案。
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
              {/* Free Plan */}
              <div className="bg-surface-container rounded-[40px] p-10 flex flex-col hover:bg-surface-bright transition-all duration-500 border border-white/5 hover:scale-[1.02] hover:shadow-2xl">
                <div className="mb-10">
                  <h3 className="text-2xl font-black mb-4">免费版</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-5xl font-black tracking-tighter font-mono">¥0</span>
                    <span className="text-on-surface-variant font-mono font-bold">/月</span>
                  </div>
                </div>
                <ul className="space-y-5 mb-12 flex-grow">
                  {["每月 3 首歌曲", "3 种可用音色", "基础视频生成", "包含水印"].map((f) => (
                    <li key={f} className="flex items-center gap-4 text-on-surface-variant font-medium">
                      <span className="material-symbols-outlined text-ember text-sm">check_circle</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <button className="w-full py-4 rounded-2xl bg-white/5 text-on-surface font-black hover:bg-white/10 active:scale-[0.98] transition-all border border-white/10">
                  免费开始
                </button>
              </div>

              {/* Recommended Plan */}
              <div className="bg-surface-container rounded-[40px] p-10 flex flex-col relative border-2 border-ember shadow-[0_20px_60px_rgba(255,107,53,0.15)] scale-[1.05] z-10">
                <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-ember text-on-primary-fixed px-6 py-1.5 rounded-full text-xs font-black tracking-[0.2em] uppercase">
                  热门推荐
                </div>
                <div className="mb-10">
                  <h3 className="text-2xl font-black mb-4 text-on-surface">创作者版</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-5xl font-black tracking-tighter font-mono text-ember">¥49</span>
                    <span className="text-on-surface-variant font-mono font-bold">/月</span>
                  </div>
                </div>
                <ul className="space-y-5 mb-12 flex-grow">
                  {["每月 30 首歌曲", "10 种可用音色", "1080P 高清视频", "无水印限制", "优先生成队列"].map((f) => (
                    <li key={f} className="flex items-center gap-4 text-on-surface font-bold">
                      <span className="material-symbols-outlined text-ember text-sm" style={{ fontVariationSettings: '"FILL" 1' }}>check_circle</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <button className="w-full py-4 rounded-2xl bg-gradient-to-r from-ember to-primary-container text-on-primary-fixed font-black hover:opacity-90 active:scale-[0.98] transition-all shadow-xl shadow-ember/30">
                  立即订阅
                </button>
              </div>

              {/* Pro Plan */}
              <div className="bg-surface-container rounded-[40px] p-10 flex flex-col hover:bg-surface-bright transition-all duration-500 border border-white/5 hover:scale-[1.02] hover:shadow-2xl">
                <div className="mb-10">
                  <h3 className="text-2xl font-black mb-4">专业版</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-5xl font-black tracking-tighter font-mono">¥149</span>
                    <span className="text-on-surface-variant font-mono font-bold">/月</span>
                  </div>
                </div>
                <ul className="space-y-5 mb-12 flex-grow">
                  {["无限歌曲/音色", "4K 电影感视频", "API 访问权限", "批量处理模式"].map((f) => (
                    <li key={f} className="flex items-center gap-4 text-on-surface-variant font-medium">
                      <span className="material-symbols-outlined text-ember text-sm">check_circle</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <button className="w-full py-4 rounded-2xl bg-white/5 text-on-surface font-black hover:bg-white/10 active:scale-[0.98] transition-all border border-white/10">
                  联系销售
                </button>
              </div>
            </div>

            {/* FAQ */}
            <div className="max-w-3xl mx-auto bg-surface-container-low rounded-[40px] p-12 md:p-16 border border-white/5 shadow-2xl">
              <h2 className="text-3xl font-black mb-16 tracking-tight text-center">常见问题解答</h2>
              <div className="space-y-8">
                {[
                  { q: "我可以随时取消吗？", a: "是的，您可以随时从您的账户设置中取消订阅。如果您在计费周期中取消，您仍可继续使用付费功能直至周期结束。" },
                  { q: "支持哪些支付方式？", a: "我们目前支持支付宝 (Alipay)、微信支付 (WeChat Pay) 以及所有主流国际信用卡。" },
                  { q: "有免费试用吗？", a: "新用户注册即可自动获得免费版权限，无需信用卡绑定。专业功能暂无免费试用，但我们提供针对创作者方案的 7 天无忧退款保证。" },
                ].map((faq, i) => (
                  <div key={i} className={`group cursor-pointer ${i > 0 ? "border-t border-white/5 pt-8" : ""}`}>
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-black text-on-surface group-hover:text-ember transition-colors">{faq.q}</span>
                      <span className="material-symbols-outlined text-on-surface-variant group-hover:text-ember transition-colors">add</span>
                    </div>
                    <div className="mt-4 text-on-surface-variant font-medium leading-relaxed">{faq.a}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-32 px-6">
          <div className="max-w-5xl mx-auto bg-gradient-to-br from-primary/30 to-secondary/10 rounded-[60px] p-16 md:p-24 text-center relative overflow-hidden border border-primary/20 shadow-[0_40px_100px_rgba(255,107,53,0.15)]">
            <div className="relative z-10">
              <h2 className="text-5xl md:text-7xl font-black mb-10 tracking-tighter">开启你的 AI 音乐之旅</h2>
              <p className="text-2xl text-on-surface-variant mb-14 max-w-2xl mx-auto font-medium">
                加入上万名创作者，让你的每一首歌都拥有千万种可能。
              </p>
              <Link
                href="/dashboard"
                prefetch={false}
                className="inline-block bg-ember text-on-primary-fixed font-black text-2xl px-16 py-6 rounded-full shadow-[0_20px_60px_rgba(255,107,53,0.4)] active:scale-[0.95] transition-all hover:shadow-[0_20px_80px_rgba(255,107,53,0.6)]"
              >
                免费开始使用
              </Link>
            </div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-primary/30 blur-[120px] -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-secondary/20 blur-[120px] translate-y-1/2 -translate-x-1/2" />
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-black border-t border-white/5 py-24 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-16 mb-20">
          <div className="col-span-2">
            <div className="text-3xl font-black text-ember mb-8">FireSing</div>
            <p className="text-on-surface-variant text-lg max-w-sm leading-relaxed font-medium">
              全球领先的 AI 音乐创作平台，专注于音色克隆与多声部协同，为创作者赋能。
            </p>
          </div>
          <div>
            <h4 className="font-black mb-8 text-white uppercase tracking-widest text-sm">产品</h4>
            <ul className="space-y-6 text-on-surface-variant font-bold">
              <li><span className="hover:text-primary transition-colors cursor-pointer">核心功能</span></li>
              <li><span className="hover:text-primary transition-colors cursor-pointer">价格方案</span></li>
              <li><span className="hover:text-primary transition-colors cursor-pointer">开发者 API</span></li>
              <li><span className="hover:text-primary transition-colors cursor-pointer">曲库展示</span></li>
            </ul>
          </div>
          <div>
            <h4 className="font-black mb-8 text-white uppercase tracking-widest text-sm">关于我们</h4>
            <ul className="space-y-6 text-on-surface-variant font-bold">
              <li><span className="hover:text-primary transition-colors cursor-pointer">公司介绍</span></li>
              <li><span className="hover:text-primary transition-colors cursor-pointer">服务条款</span></li>
              <li><span className="hover:text-primary transition-colors cursor-pointer">隐私政策</span></li>
              <li><span className="hover:text-primary transition-colors cursor-pointer">联系我们</span></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto pt-10 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="text-sm text-on-surface-variant font-bold font-mono">&copy; 2025 The Obsidian Studio. 版权所有.</div>
          <div className="flex gap-8">
            <span className="text-on-surface-variant hover:text-white transition-all transform hover:scale-110 cursor-pointer"><span className="material-symbols-outlined">language</span></span>
            <span className="text-on-surface-variant hover:text-white transition-all transform hover:scale-110 cursor-pointer"><span className="material-symbols-outlined">mail</span></span>
            <span className="text-on-surface-variant hover:text-white transition-all transform hover:scale-110 cursor-pointer"><span className="material-symbols-outlined">podcasts</span></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
