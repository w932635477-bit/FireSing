import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="bg-surface-container-lowest text-on-surface">
      {/* Top Navigation */}
      <header className="fixed top-0 w-full flex justify-between items-center px-6 py-4 bg-black/60 backdrop-blur-xl z-50 shadow-[0_8px_32px_rgba(255,107,53,0.15)]">
        <div className="text-2xl font-black text-ember tracking-tight">FireSing</div>
        <nav className="hidden md:flex gap-8 items-center">
          <Link href="/" className="text-ember font-bold border-b-2 border-ember">首页</Link>
          <Link href="/dashboard" className="text-white/60 font-medium hover:bg-white/10 px-3 py-1 rounded transition-colors">工作台</Link>
          <Link href="/dashboard" className="text-white/60 font-medium hover:bg-white/10 px-3 py-1 rounded transition-colors">曲库</Link>
          <span className="text-white/60 font-medium hover:bg-white/10 px-3 py-1 rounded transition-colors cursor-pointer">会员方案</span>
        </nav>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="bg-ember text-on-primary-fixed font-bold px-5 py-2 rounded shadow-[0_8px_32px_rgba(255,107,53,0.15)] active:scale-[0.98] transition-transform"
          >
            上传新歌
          </Link>
          <Link href="/login" className="w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-white/10 flex items-center justify-center">
            <span className="material-symbols-outlined text-white/60">person</span>
          </Link>
        </div>
      </header>

      <main className="pt-0">
        {/* Hero Section */}
        <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 overflow-hidden">
          {/* Background layers */}
          <div className="absolute inset-0 z-0">
            {/* Ambient color orbs */}
            <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-ember/8 rounded-full blur-[150px]" />
            <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[130px]" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/3 rounded-full blur-[200px]" />
            {/* Subtle grid pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,107,53,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,107,53,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
          </div>
          <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black z-[1]" />
          {/* Decorative sound wave lines (visible on all screens) */}
          <div className="absolute bottom-[15%] left-0 right-0 z-[2] flex items-end justify-center gap-[3px] h-32 opacity-20">
            {[40, 65, 90, 55, 80, 45, 70, 95, 60, 50, 85, 35, 75, 60, 90, 45, 70, 55, 80, 65].map((h, i) => (
              <div key={i} className="w-1.5 bg-gradient-to-t from-ember to-primary rounded-full" style={{ height: `${h}%` }} />
            ))}
          </div>
          <div className="relative z-10 max-w-4xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest mb-8 animate-pulse">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
              </span>
              全新 AI 引擎已上线
            </div>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-8 bg-gradient-to-b from-white to-white/40 bg-clip-text text-transparent drop-shadow-2xl">
              一首歌，十种声音
            </h1>
            <p className="text-xl md:text-2xl text-on-surface-variant mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
              AI 驱动的多人多音色翻唱平台，重新定义您的音乐创作可能。
            </p>
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Link
                href="/dashboard"
                className="bg-ember text-on-primary font-black text-xl px-12 py-5 rounded-full shadow-[0_12px_48px_rgba(255,107,53,0.4)] active:scale-[0.98] transition-all hover:shadow-[0_12px_64px_rgba(255,107,53,0.6)]"
              >
                立即体验
              </Link>
              <button className="bg-white/10 backdrop-blur-md text-on-surface font-bold text-xl px-12 py-5 rounded-full border border-white/20 hover:bg-white/20 active:scale-[0.98] transition-all flex items-center gap-2">
                查看演示 <span className="material-symbols-outlined">play_circle</span>
              </button>
            </div>
          </div>

          {/* Floating Song Preview Cards - mobile simplified version */}
          <div className="relative w-full max-w-sm mt-16 h-48 lg:hidden">
            <div className="w-full bg-surface-container/80 backdrop-blur-xl p-5 rounded-2xl border border-primary/20 shadow-[0_0_40px_rgba(255,107,53,0.15)]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary">equalizer</span>
                </div>
                <div className="text-left">
                  <div className="font-bold text-sm">AI 音色处理中</div>
                  <div className="text-xs text-on-surface-variant font-mono">85%</div>
                </div>
              </div>
              <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden p-[1px]">
                <div className="bg-gradient-to-r from-ember to-primary-container h-full w-[85%] rounded-full" />
              </div>
            </div>
          </div>

          {/* Floating Song Preview Cards - desktop */}
          <div className="relative w-full max-w-6xl mt-24 h-64 hidden lg:block">
            {/* Card 1 */}
            <div className="absolute top-0 left-0 w-72 bg-surface-container-high/40 backdrop-blur-2xl p-4 rounded-2xl border border-white/10 shadow-2xl -rotate-6 animate-float">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-primary">music_note</span>
                </div>
                <div className="text-left">
                  <div className="font-bold text-sm">珊瑚海</div>
                  <div className="text-xs text-on-surface-variant font-mono">03:42</div>
                </div>
              </div>
              <div className="flex items-end gap-[3px] h-12 mb-3">
                <div className="flex-1 bg-primary/40 h-1/2 rounded-full animate-pulse" />
                <div className="flex-1 bg-primary/60 h-3/4 rounded-full animate-pulse" style={{ animationDelay: "0.1s" }} />
                <div className="flex-1 bg-primary h-full rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
                <div className="flex-1 bg-primary/80 h-2/3 rounded-full animate-pulse" style={{ animationDelay: "0.3s" }} />
                <div className="flex-1 bg-primary/50 h-1/3 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
                <div className="flex-1 bg-primary/70 h-3/4 rounded-full animate-pulse" style={{ animationDelay: "0.5s" }} />
              </div>
              <div className="flex gap-2">
                <div className="w-5 h-5 rounded-full border-2 border-white/20 bg-secondary" />
                <div className="w-5 h-5 rounded-full border-2 border-white/20 bg-tertiary" />
                <div className="w-5 h-5 rounded-full border-2 border-white/20 bg-error" />
              </div>
            </div>

            {/* Card 2 (Active) */}
            <div className="absolute top-10 left-1/2 -translate-x-1/2 w-80 bg-surface-container p-6 rounded-2xl border border-primary/30 shadow-[0_0_80px_rgba(255,107,53,0.2)] z-20">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-lg font-bold">稻香</h3>
                  <p className="text-sm text-on-surface-variant">原唱：周杰伦</p>
                </div>
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: '"FILL" 1' }}>equalizer</span>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs font-mono text-on-surface-variant font-bold">
                  <span>AI 音色分配中...</span>
                  <span className="text-primary">85%</span>
                </div>
                <div className="w-full bg-surface-container-highest h-3 rounded-full overflow-hidden p-[2px]">
                  <div className="bg-gradient-to-r from-primary to-primary-container h-full w-[85%] rounded-full shadow-[0_0_12px_rgba(255,107,53,0.5)]" />
                </div>
              </div>
            </div>

            {/* Card 3 */}
            <div className="absolute top-0 right-0 w-72 bg-surface-container-high/40 backdrop-blur-2xl p-4 rounded-2xl border border-white/10 shadow-2xl rotate-6 animate-float" style={{ animationDelay: "1s" }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-secondary rounded-xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-secondary">mic</span>
                </div>
                <div className="text-left">
                  <div className="font-bold text-sm">晴天</div>
                  <div className="text-xs text-on-surface-variant font-mono">处理完毕</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="h-2 bg-secondary/20 rounded-full" />
                <div className="h-2 bg-secondary rounded-full" />
                <div className="h-2 bg-secondary/40 rounded-full" />
                <div className="h-2 bg-secondary/10 rounded-full" />
              </div>
            </div>
          </div>
        </section>

        {/* Three-Step Guide */}
        <section className="py-32 px-6 max-w-7xl mx-auto">
          <h2 className="text-5xl font-black mb-20 text-center tracking-tight">创作流程</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {/* Step 01: Upload */}
            <div className="group relative">
              <div className="absolute -inset-4 bg-gradient-to-b from-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-3xl -z-10" />
              <div className="aspect-square bg-surface-container-low rounded-3xl p-10 flex flex-col justify-between transition-all group-hover:translate-y-[-8px] group-hover:bg-surface-container border border-white/5">
                <div className="w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/20">
                  <span className="material-symbols-outlined text-5xl">cloud_upload</span>
                </div>
                <div>
                  <span className="text-primary font-black font-mono text-6xl opacity-10 block mb-4">01</span>
                  <h3 className="text-3xl font-black mb-3 text-white tracking-tight">上传</h3>
                  <p className="text-on-surface-variant text-lg font-medium">拖拽上传 音频+歌词</p>
                </div>
              </div>
            </div>
            {/* Step 02: Assign */}
            <div className="group relative">
              <div className="absolute -inset-4 bg-gradient-to-b from-secondary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-3xl -z-10" />
              <div className="aspect-square bg-surface-container-low rounded-3xl p-10 flex flex-col justify-between transition-all group-hover:translate-y-[-8px] group-hover:bg-surface-container border border-white/5">
                <div className="w-20 h-20 bg-secondary/10 rounded-2xl flex items-center justify-center text-secondary border border-secondary/20">
                  <span className="material-symbols-outlined text-5xl">auto_awesome</span>
                </div>
                <div>
                  <span className="text-secondary font-black font-mono text-6xl opacity-10 block mb-4">02</span>
                  <h3 className="text-3xl font-black mb-3 text-white tracking-tight">分配</h3>
                  <p className="text-on-surface-variant text-lg font-medium">AI 自动分配 或手动选择</p>
                </div>
              </div>
            </div>
            {/* Step 03: Generate */}
            <div className="group relative">
              <div className="absolute -inset-4 bg-gradient-to-b from-tertiary-dim/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-3xl -z-10" />
              <div className="aspect-square bg-surface-container-low rounded-3xl p-10 flex flex-col justify-between transition-all group-hover:translate-y-[-8px] group-hover:bg-surface-container border border-white/5">
                <div className="w-20 h-20 bg-tertiary-dim/10 rounded-2xl flex items-center justify-center text-tertiary-dim border border-tertiary-dim/20">
                  <span className="material-symbols-outlined text-5xl">movie</span>
                </div>
                <div>
                  <span className="text-tertiary-dim font-black font-mono text-6xl opacity-10 block mb-4">03</span>
                  <h3 className="text-3xl font-black mb-3 text-white tracking-tight">生成</h3>
                  <p className="text-on-surface-variant text-lg font-medium">竖版视频 一键下载</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Grid (Bento) */}
        <section className="py-32 px-6 bg-surface-container-low/50">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 auto-rows-[280px]">
              {/* Large Feature */}
              <div className="md:col-span-8 md:row-span-2 bg-surface-container rounded-[40px] p-12 flex flex-col justify-between overflow-hidden relative border border-white/5 group">
                <div className="relative z-10">
                  <span className="text-primary font-black text-sm uppercase tracking-[0.2em] mb-6 block">专业级表现</span>
                  <h3 className="text-5xl font-black mb-6 max-w-md leading-tight">
                    多人合唱模式<br />
                    <span className="text-primary">Multi-voice chorus</span>
                  </h3>
                  <p className="text-on-surface-variant text-xl max-w-sm font-medium leading-relaxed">
                    突破单人翻唱限制，为每个段落分配专属音色，打造属于你的虚拟乐团。
                  </p>
                </div>
                <div className="absolute bottom-[-10%] right-[-5%] w-3/4 opacity-20 group-hover:scale-110 transition-transform duration-700 bg-gradient-to-br from-ember/30 to-secondary/20 rounded-3xl rotate-6 aspect-video" />
              </div>

              {/* Vertical Video */}
              <div className="md:col-span-4 md:row-span-2 bg-surface-container rounded-[40px] p-12 flex flex-col justify-between border border-white/5">
                <div>
                  <h3 className="text-3xl font-black mb-6 tracking-tight">竖版视频生成</h3>
                  <p className="text-on-surface-variant text-lg font-medium">
                    生成适配抖音/Shorts的竖版音乐视频，自带动态歌词效果。
                  </p>
                </div>
                <div className="flex-1 mt-10 bg-surface-container-lowest rounded-3xl border border-white/5 flex items-center justify-center p-4">
                  <div className="w-full aspect-[9/16] bg-primary/10 rounded-2xl border-2 border-primary/20 flex items-center justify-center shadow-inner">
                    <span className="material-symbols-outlined text-primary text-6xl animate-pulse">play_circle</span>
                  </div>
                </div>
              </div>

              {/* Monologue */}
              <div className="md:col-span-6 bg-surface-container rounded-[40px] p-12 flex items-center gap-10 border border-white/5 hover:bg-surface-bright transition-colors">
                <div className="w-24 h-24 bg-secondary/10 rounded-full flex-shrink-0 flex items-center justify-center border border-secondary/20">
                  <span className="material-symbols-outlined text-secondary text-5xl">record_voice_over</span>
                </div>
                <div>
                  <h3 className="text-2xl font-black mb-3">个性化独白</h3>
                  <p className="text-on-surface-variant text-lg font-medium">插入个性化独白，让作品更具情感深度。</p>
                </div>
              </div>

              {/* Preservation */}
              <div className="md:col-span-6 bg-surface-container rounded-[40px] p-12 flex items-center gap-10 border border-white/5 hover:bg-surface-bright transition-colors">
                <div className="w-24 h-24 bg-tertiary/10 rounded-full flex-shrink-0 flex items-center justify-center border border-tertiary/20">
                  <span className="material-symbols-outlined text-tertiary text-5xl">settings_input_component</span>
                </div>
                <div>
                  <h3 className="text-2xl font-black mb-3">原声细节保留</h3>
                  <p className="text-on-surface-variant text-lg font-medium">完美保留原曲混响与动态，高保真还原音质。</p>
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
              <div className="bg-surface-container rounded-[32px] p-10 flex flex-col hover:bg-surface-bright transition-all duration-500 border border-white/5 hover:scale-[1.02] hover:shadow-2xl">
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
              <div className="bg-surface-container rounded-[32px] p-10 flex flex-col relative border-2 border-ember shadow-[0_20px_60px_rgba(255,107,53,0.15)] scale-[1.05] z-10">
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
              <div className="bg-surface-container rounded-[32px] p-10 flex flex-col hover:bg-surface-bright transition-all duration-500 border border-white/5 hover:scale-[1.02] hover:shadow-2xl">
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
          <div className="text-sm text-on-surface-variant font-bold font-mono">© 2025 The Obsidian Studio. 版权所有.</div>
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
