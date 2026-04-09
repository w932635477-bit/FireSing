import Link from "next/link";
import Image from "next/image";

export default function BelowFold() {
  return (
    <>
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
            <span className="text-ember font-bold text-sm uppercase tracking-[0.3em] font-mono mb-4 block">如何运作</span>
            <h2 className="text-5xl md:text-6xl font-black tracking-tighter">三步完成创作</h2>
          </div>

          <div className="relative">
            {/* Flow connector line (desktop only) */}
            <div className="hidden md:block absolute top-1/2 left-0 right-0 h-px -translate-y-1/2 z-0">
              <div className="h-full bg-gradient-to-r from-ember/30 via-secondary/30 to-tertiary-dim/30" />
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
                <div className="absolute -inset-1 bg-gradient-to-br from-ember/20 via-transparent to-ember/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-all duration-500 blur-sm" />
                <div className="relative bg-surface-container rounded-2xl overflow-hidden border border-white/5 group-hover:border-ember/20 transition-all duration-500">
                  <Image src="/images/step-upload.webp" alt="" fill sizes="400px" className="object-cover opacity-25 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/40" />
                  <div className="absolute inset-0 bg-ember/5 group-hover:bg-ember/10 transition-colors duration-500" />
                  <div className="absolute inset-0 bg-[linear-gradient(rgba(255,107,53,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,107,53,0.02)_1px,transparent_1px)] bg-[size:40px_40px] opacity-30" />
                  <div className="relative z-10 p-10">
                    <div className="flex items-start justify-between mb-12">
                      <div className="relative">
                        <div className="absolute inset-0 bg-ember/20 rounded-2xl blur-xl animate-glow-pulse" />
                        <div className="relative w-16 h-16 bg-gradient-to-br from-ember/20 to-ember/5 rounded-2xl flex items-center justify-center border border-ember/20">
                          <span className="material-symbols-outlined text-ember text-3xl">cloud_upload</span>
                        </div>
                      </div>
                      <span className="text-ember/20 font-black font-mono text-7xl leading-none select-none">01</span>
                    </div>
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
                <div className="absolute -inset-1 bg-gradient-to-br from-secondary/20 via-transparent to-secondary/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-all duration-500 blur-sm" />
                <div className="relative bg-surface-container rounded-2xl overflow-hidden border border-white/5 group-hover:border-secondary/20 transition-all duration-500">
                  <Image src="/images/step-assign.webp" alt="" fill sizes="400px" className="object-cover opacity-25 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/40" />
                  <div className="absolute inset-0 bg-secondary/5 group-hover:bg-secondary/10 transition-colors duration-500" />
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
                <div className="absolute -inset-1 bg-gradient-to-br from-tertiary-dim/20 via-transparent to-tertiary-dim/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-all duration-500 blur-sm" />
                <div className="relative bg-surface-container rounded-2xl overflow-hidden border border-white/5 group-hover:border-tertiary-dim/20 transition-all duration-500">
                  <Image src="/images/step-generate.webp" alt="" fill sizes="400px" className="object-cover opacity-25 group-hover:opacity-40 group-hover:scale-105 transition-all duration-700" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/40" />
                  <div className="absolute inset-0 bg-tertiary-dim/5 group-hover:bg-tertiary-dim/10 transition-colors duration-500" />
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

      {/* Feature Grid (Bento) */}
      <section className="py-32 px-6 bg-surface-container-low/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 auto-rows-[280px]">
            <div className="md:col-span-8 md:row-span-2 bg-surface-container rounded-2xl overflow-hidden relative border border-white/5 group">
              <Image src="/images/chorus-feature.webp" alt="AI 多人合唱模式" fill sizes="(max-width: 768px) 100vw, 66vw" className="object-cover opacity-40 group-hover:opacity-50 group-hover:scale-105 transition-all duration-700" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
              <div className="relative z-10 h-full flex flex-col justify-end p-12">
                <span className="text-ember font-black text-sm uppercase tracking-[0.2em] mb-4 block">专业级表现</span>
                <h3 className="text-4xl md:text-5xl font-black mb-4 leading-tight">多人合唱模式<br /><span className="text-ember">多人合唱</span></h3>
                <p className="text-on-surface-variant text-lg max-w-md font-medium leading-relaxed">突破单人翻唱限制，为每个段落分配专属音色，打造属于你的虚拟乐团。</p>
              </div>
            </div>

            <div className="md:col-span-4 md:row-span-2 bg-surface-container rounded-2xl overflow-hidden relative border border-white/5">
              <Image src="/images/vertical-video-feature.webp" alt="竖版视频生成" fill sizes="(max-width: 768px) 100vw, 33vw" className="object-cover opacity-30" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent" />
              <div className="relative z-10 h-full flex flex-col justify-between p-10">
                <div>
                  <h3 className="text-2xl font-black mb-3 tracking-tight">竖版视频生成</h3>
                  <p className="text-on-surface-variant text-sm font-medium">适配抖音/Shorts的竖版音乐视频，自带动态歌词效果。</p>
                </div>
                <div className="flex items-center gap-3 mt-auto">
                  <span className="material-symbols-outlined text-ember text-3xl">play_circle</span>
                  <span className="text-ember font-bold text-sm">查看示例</span>
                </div>
              </div>
            </div>

            <div className="md:col-span-6 bg-surface-container rounded-2xl overflow-hidden relative border border-white/5 hover:bg-surface-bright transition-colors group">
              <Image src="/images/monologue-feature.webp" alt="个性化独白" fill sizes="(max-width: 768px) 100vw, 50vw" className="object-cover opacity-20 group-hover:opacity-30 transition-opacity duration-500" />
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

            <div className="md:col-span-6 bg-surface-container rounded-2xl overflow-hidden relative border border-white/5 hover:bg-surface-bright transition-colors group">
              <Image src="/images/preservation-feature.webp" alt="原声细节保留" fill sizes="(max-width: 768px) 100vw, 50vw" className="object-cover opacity-20 group-hover:opacity-30 transition-opacity duration-500" />
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

      {/* Pricing - CTA to pricing page */}
      <section className="py-32 px-6 bg-surface-container-low/30">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-black tracking-tighter mb-8">按需付费，用多少买多少</h2>
          <p className="text-on-surface-variant text-xl max-w-2xl mx-auto font-medium mb-12">新用户注册送 3 首。无需订阅，一首歌一首歌地买。</p>
          <Link href="/pricing" className="inline-block bg-ember text-on-primary-fixed font-black text-lg px-10 py-4 rounded-xl shadow-[0_8px_40px_rgba(255,107,53,0.4)] active:scale-[0.98] transition-all hover:shadow-[0_12px_60px_rgba(255,107,53,0.6)]">查看定价方案</Link>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-32 px-6">
        <div className="max-w-5xl mx-auto bg-gradient-to-br from-primary/30 to-secondary/10 rounded-2xl p-16 md:p-24 text-center relative overflow-hidden border border-white/5 shadow-[0_40px_100px_rgba(255,107,53,0.15)]">
          <div className="relative z-10">
            <h2 className="text-5xl md:text-7xl font-black mb-10 tracking-tighter">给你的老歌一个新声音</h2>
            <p className="text-2xl text-on-surface-variant mb-14 max-w-2xl mx-auto font-medium">上传一首歌，选几种音色，两分钟拿翻唱视频。就这么简单。</p>
            <Link href="/dashboard" prefetch={false} className="inline-block bg-ember text-on-primary-fixed font-black text-2xl px-16 py-6 rounded-full shadow-[0_20px_60px_rgba(255,107,53,0.4)] active:scale-[0.95] transition-all hover:shadow-[0_20px_80px_rgba(255,107,53,0.6)]">免费开始使用</Link>
          </div>
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary/30 blur-[120px] -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-secondary/20 blur-[120px] translate-y-1/2 -translate-x-1/2" />
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black border-t border-white/5 py-16 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div>
            <div className="text-2xl font-black text-ember mb-2">FireSing</div>
            <p className="text-sm text-on-surface-variant font-medium">老歌魔改平台 · AI 方言翻唱</p>
          </div>
          <nav className="flex gap-8 text-on-surface-variant font-bold text-sm">
            <Link href="/#how-it-works" className="hover:text-primary transition-colors">功能介绍</Link>
            <Link href="/pricing" className="hover:text-primary transition-colors">定价</Link>
            <Link href="/dashboard" prefetch={false} className="hover:text-primary transition-colors">我的作品</Link>
          </nav>
          <div className="text-sm text-on-surface-variant font-mono">&copy; 2026 FireSing</div>
        </div>
      </footer>
    </>
  );
}
