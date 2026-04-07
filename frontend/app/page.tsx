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
          <Link href="/dashboard" prefetch={false} className="text-white/60 font-medium hover:bg-white/10 px-3 py-2 rounded transition-colors">我的作品</Link>
          <span className="text-white/40 font-medium px-3 py-2 cursor-not-allowed">音乐库 <span className="text-[9px] text-white/20">即将上线</span></span>
          <span className="text-white/40 font-medium px-3 py-2 cursor-not-allowed">会员方案 <span className="text-[9px] text-white/20">即将上线</span></span>
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
                  <span className="opacity-40 cursor-not-allowed bg-white/5 backdrop-blur-md text-on-surface font-bold text-lg px-10 py-4 rounded-lg border border-white/5 flex items-center gap-2">
                    查看演示 <span className="text-[9px] text-on-surface-variant/40">即将上线</span>
                  </span>
                </div>

                {/* Status row */}
                <div className="flex gap-10 mt-14">
                  <div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                      <span className="text-sm font-bold text-success">内测中</span>
                    </div>
                    <div className="text-xs text-on-surface-variant font-medium uppercase tracking-wider mt-1">Beta</div>
                  </div>
                  <div>
                    <div className="text-2xl md:text-3xl font-black text-ember font-mono">RVC</div>
                    <div className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">AI 语音引擎</div>
                  </div>
                  <div>
                    <div className="text-2xl md:text-3xl font-black text-ember font-mono">9:16</div>
                    <div className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">竖版视频</div>
                  </div>
                </div>
              </div>

              {/* Right: Community works placeholder */}
              <div className="lg:col-span-5 relative hidden lg:flex items-center justify-center">
                <div className="text-center opacity-40">
                  <span className="material-symbols-outlined text-6xl text-ember/40 mb-4 block">queue_music</span>
                  <p className="text-sm font-bold text-on-surface-variant/60">社区作品即将上线</p>
                  <p className="text-xs text-on-surface-variant/40 mt-1">内测阶段，敬请期待</p>
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

        {/* Beta CTA - replaces pricing during MVP */}
        <section className="py-32 px-6 bg-surface-container-low/30" id="pricing">
          <div className="max-w-3xl mx-auto">
            <div className="bg-surface-container rounded-[40px] p-12 md:p-16 border border-ember/20 text-center relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-ember/10 rounded-full blur-[100px]" />
              <div className="relative z-10">
                <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-ember/10 border border-ember/20 text-ember text-xs font-bold uppercase tracking-widest mb-8">
                  <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                  内测阶段 · 免费使用
                </span>
                <h2 className="text-4xl md:text-5xl font-black tracking-tighter mb-6">产品处于内测阶段</h2>
                <p className="text-on-surface-variant text-lg max-w-xl mx-auto font-medium leading-relaxed mb-10">
                  目前所有功能免费开放。正式上线后将推出免费版、创作者版和专业版方案。
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left mb-10">
                  {[
                    { name: "免费版", features: "3 首歌/月 · 3 种音色 · 含水印" },
                    { name: "创作者版", features: "30 首/月 · 10 种音色 · 1080P · ¥49/月" },
                    { name: "专业版", features: "无限量 · 4K 视频 · API · ¥149/月" },
                  ].map((plan) => (
                    <div key={plan.name} className="bg-surface-container-high/50 rounded-xl p-4 border border-white/5">
                      <div className="text-sm font-black text-ember mb-1">{plan.name}</div>
                      <div className="text-xs text-on-surface-variant">{plan.features}</div>
                    </div>
                  ))}
                </div>
                <Link
                  href="/dashboard"
                  prefetch={false}
                  className="inline-block bg-ember text-on-primary-fixed font-black px-10 py-4 rounded-xl shadow-[0_8px_40px_rgba(255,107,53,0.3)] active:scale-[0.98] transition-all"
                >
                  免费开始使用
                </Link>
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
                AI 驱动的多人多音色翻唱平台，让你的每一首歌都拥有千万种可能。
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
              <li><span className="cursor-default">核心功能</span></li>
              <li><span className="cursor-default">价格方案</span></li>
              <li><span className="cursor-default">开发者 API</span></li>
              <li><span className="cursor-default">曲库展示</span></li>
            </ul>
          </div>
          <div>
            <h4 className="font-black mb-8 text-white uppercase tracking-widest text-sm">关于我们</h4>
            <ul className="space-y-6 text-on-surface-variant font-bold">
              <li><span className="cursor-default">公司介绍</span></li>
              <li><span className="cursor-default">服务条款</span></li>
              <li><span className="cursor-default">隐私政策</span></li>
              <li><span className="cursor-default">联系我们</span></li>
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
