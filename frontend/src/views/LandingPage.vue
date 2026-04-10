<template>
  <div class="landing">
    <!-- Hero -->
    <section class="hero-section d-flex align-center justify-center" style="min-height: 100vh; position: relative; overflow: hidden;">
      <div class="pulse-bg">
        <div class="pulse-ring pulse-ring-1"></div>
        <div class="pulse-ring pulse-ring-2"></div>
        <div class="pulse-ring pulse-ring-3"></div>
      </div>

      <v-container class="text-center hero-content">
        <v-chip color="primary" variant="tonal" size="small" class="mb-4 mb-md-6">{{ t("landing.heroChip") }}</v-chip>
        <h1 class="text-h3 text-sm-h2 text-md-h1 font-weight-black mb-4 hero-title">
          Pulse<span class="gradient-text">ID</span>
        </h1>
        <p class="text-body-1 text-sm-h6 text-medium-emphasis mx-auto mb-3" style="max-width: 720px; line-height: 1.8;">
          {{ t("landing.heroSubtitle1") }}
        </p>
        <p class="text-body-2 text-sm-body-1 text-medium-emphasis mx-auto mb-6 mb-md-8" style="max-width: 600px;">
          {{ t("landing.heroSubtitle2") }}
        </p>
        <div class="d-flex justify-center ga-3 ga-sm-4 flex-wrap">
          <v-btn size="large" color="primary" variant="flat" to="/login" prepend-icon="mdi-monitor-dashboard" rounded="lg" class="px-6 px-sm-8 hero-btn">
            {{ t("landing.onlineDemo") }}
          </v-btn>
          <v-btn size="large" variant="outlined" color="white" href="https://github.com/2RL-AI/PulseID" target="_blank" prepend-icon="mdi-github" rounded="lg" class="px-6 px-sm-8 hero-btn">
            {{ t("landing.viewGithub") }}
          </v-btn>
        </div>
        <div class="d-flex justify-center ga-6 ga-sm-10 mt-10 mt-md-14 flex-wrap stats-row">
          <div class="text-center"><div class="text-h5 text-sm-h4 font-weight-bold gradient-text">NFC</div><div class="text-caption text-medium-emphasis">{{ t("landing.statsNfc") }}</div></div>
          <div class="text-center"><div class="text-h5 text-sm-h4 font-weight-bold gradient-text">REST</div><div class="text-caption text-medium-emphasis">{{ t("landing.statsRest") }}</div></div>
          <div class="text-center"><div class="text-h5 text-sm-h4 font-weight-bold gradient-text">PDF</div><div class="text-caption text-medium-emphasis">{{ t("landing.statsPdf") }}</div></div>
          <div class="text-center"><div class="text-h5 text-sm-h4 font-weight-bold gradient-text">EU</div><div class="text-caption text-medium-emphasis">{{ t("landing.statsEu") }}</div></div>
        </div>
      </v-container>
      <div class="scroll-indicator d-none d-sm-block"><v-icon icon="mdi-chevron-down" size="28" color="primary" class="bounce" /></div>
    </section>

    <!-- Why PulseID -->
    <section class="section-padding" style="background: rgba(99, 102, 241, 0.03);">
      <v-container>
        <v-row align="center" class="flex-column-reverse flex-md-row">
          <v-col cols="12" md="7">
            <v-chip color="warning" variant="tonal" size="small" class="mb-4">{{ t("landing.whyChip") }}</v-chip>
            <h2 class="text-h4 text-sm-h3 font-weight-bold mb-4">{{ t("landing.whyTitle") }}</h2>
            <p class="text-body-1 text-medium-emphasis mb-4" style="line-height: 1.85;">{{ t("landing.whyP1") }}</p>
            <p class="text-body-1 text-medium-emphasis mb-4" style="line-height: 1.85;">{{ t("landing.whyP2") }}</p>
            <p class="text-body-1 text-medium-emphasis mb-6" style="line-height: 1.85;">{{ t("landing.whyP3") }}</p>
            <div class="d-flex ga-2 ga-sm-3 flex-wrap">
              <v-chip variant="tonal" color="success" prepend-icon="mdi-check" size="small">{{ t("landing.whyLux") }}</v-chip>
              <v-chip variant="tonal" color="success" prepend-icon="mdi-check" size="small">{{ t("landing.whyEu") }}</v-chip>
              <v-chip variant="tonal" color="success" prepend-icon="mdi-check" size="small">{{ t("landing.whyGdpr") }}</v-chip>
              <v-chip variant="tonal" color="success" prepend-icon="mdi-check" size="small">{{ t("landing.whyItm") }}</v-chip>
            </div>
          </v-col>
          <v-col cols="12" md="5" class="mb-6 mb-md-0">
            <v-card variant="flat" rounded="xl" class="pa-6 pa-sm-8 compliance-card text-center mb-4">
              <v-icon icon="mdi-scale-balance" size="64" color="primary" class="mb-3" />
              <h3 class="text-h6 font-weight-bold mb-2">{{ t("landing.complianceTitle") }}</h3>
              <p class="text-body-2 text-medium-emphasis" style="line-height: 1.7;">{{ t("landing.complianceDesc") }}</p>
            </v-card>
            <v-card variant="flat" rounded="xl" class="pa-6 pa-sm-8 compliance-card text-center">
              <v-icon icon="mdi-domain" size="64" color="secondary" class="mb-3" />
              <h3 class="text-h6 font-weight-bold mb-2">{{ t("landing.smeTitle") }}</h3>
              <p class="text-body-2 text-medium-emphasis" style="line-height: 1.7;">{{ t("landing.smeDesc") }}</p>
              <div class="d-flex justify-center ga-1 flex-wrap mt-3">
                <v-chip v-for="type in ['SARL', 'SARL-S', 'SA', 'SAS', 'GmbH']" :key="type" variant="tonal" color="secondary" size="small">{{ type }}</v-chip>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- Features -->
    <section id="features" class="section-padding">
      <v-container>
        <div class="text-center mb-8 mb-md-12">
          <v-chip color="primary" variant="tonal" size="small" class="mb-4">{{ t("landing.featuresChip") }}</v-chip>
          <h2 class="text-h4 text-sm-h3 font-weight-bold mb-3">{{ t("landing.featuresTitle") }}</h2>
          <p class="text-body-1 text-medium-emphasis mx-auto" style="max-width: 620px; line-height: 1.7;">{{ t("landing.featuresSubtitle") }}</p>
        </div>
        <v-row justify="center">
          <v-col v-for="feat in features" :key="feat.titleKey" cols="12" sm="6" lg="3">
            <v-card class="feature-card pa-5 pa-sm-6 text-center" variant="outlined" rounded="xl" height="100%">
              <v-avatar size="64" :color="feat.color" variant="tonal" class="mb-4"><v-icon :icon="feat.icon" size="32" /></v-avatar>
              <h3 class="text-subtitle-1 text-sm-h6 font-weight-bold mb-2">{{ t(feat.titleKey) }}</h3>
              <p class="text-body-2 text-medium-emphasis" style="line-height: 1.6;">{{ t(feat.descKey) }}</p>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- How It Works -->
    <section class="section-padding" style="background: rgba(99, 102, 241, 0.03);">
      <v-container>
        <div class="text-center mb-8 mb-md-12">
          <v-chip color="secondary" variant="tonal" size="small" class="mb-4">{{ t("landing.howChip") }}</v-chip>
          <h2 class="text-h4 text-sm-h3 font-weight-bold mb-3">{{ t("landing.howTitle") }}</h2>
          <p class="text-body-1 text-medium-emphasis mx-auto" style="max-width: 540px;">{{ t("landing.howSubtitle") }}</p>
        </div>
        <v-row justify="center">
          <v-col v-for="(step, i) in steps" :key="step.titleKey" cols="12" sm="6" lg="3">
            <div class="text-center px-2 px-sm-4">
              <v-avatar size="72" color="primary" variant="tonal" class="mb-4"><span class="text-h5 font-weight-bold">{{ i + 1 }}</span></v-avatar>
              <h3 class="text-subtitle-1 text-sm-h6 font-weight-bold mb-2">{{ t(step.titleKey) }}</h3>
              <p class="text-body-2 text-medium-emphasis" style="line-height: 1.6;">{{ t(step.descKey) }}</p>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- Pricing -->
    <section class="section-padding">
      <v-container>
        <div class="text-center mb-8 mb-md-12">
          <v-chip color="success" variant="tonal" size="small" class="mb-4">{{ t("landing.pricingChip") }}</v-chip>
          <h2 class="text-h4 text-sm-h3 font-weight-bold mb-3">{{ t("landing.pricingTitle") }}</h2>
          <p class="text-body-1 text-medium-emphasis mx-auto" style="max-width: 580px; line-height: 1.7;">{{ t("landing.pricingSubtitle") }}</p>
        </div>
        <v-row justify="center">
          <v-col cols="12" sm="10" md="8" lg="6">
            <v-card variant="outlined" rounded="xl" class="pricing-card pa-6 pa-sm-8">
              <div class="text-center mb-6">
                <div class="text-caption text-medium-emphasis text-uppercase font-weight-bold mb-1" style="letter-spacing: 0.1em;">{{ t("landing.pricingLabel") }}</div>
                <div class="text-h3 font-weight-black gradient-text">499&euro;</div>
                <div class="text-body-2 text-medium-emphasis">{{ t("landing.pricingSetup") }}</div>
              </div>
              <v-divider class="mb-6 border-opacity-10" />
              <div class="mb-6">
                <div class="text-subtitle-2 font-weight-bold mb-3">{{ t("landing.pricingIncluded") }}</div>
                <v-list density="compact" class="bg-transparent">
                  <v-list-item v-for="i in 6" :key="i" prepend-icon="mdi-check-circle" class="px-0">
                    <v-list-item-title class="text-body-2">{{ t(`landing.pricingItem${i}`) }}</v-list-item-title>
                  </v-list-item>
                </v-list>
              </div>
              <v-divider class="mb-6 border-opacity-10" />
              <v-row dense class="text-center mb-6">
                <v-col cols="6">
                  <div class="text-h5 font-weight-bold">99&euro;</div>
                  <div class="text-caption text-medium-emphasis">{{ t("landing.pricingYear") }}</div>
                </v-col>
                <v-col cols="6">
                  <div class="text-h5 font-weight-bold">10&euro;</div>
                  <div class="text-caption text-medium-emphasis">{{ t("landing.pricingBadge") }}</div>
                </v-col>
              </v-row>
              <v-btn block size="large" color="primary" href="mailto:contact@2rl.ai" rounded="lg" prepend-icon="mdi-email-outline">
                {{ t("landing.pricingContact") }}
              </v-btn>
              <div class="text-center mt-4">
                <v-chip variant="tonal" color="info" size="small" prepend-icon="mdi-map-marker">
                  {{ t("landing.pricingAvailability") }}
                </v-chip>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- CTA -->
    <section class="section-padding" style="background: rgba(99, 102, 241, 0.03);">
      <v-container>
        <v-card class="cta-card pa-8 pa-sm-12 text-center" rounded="xl" variant="flat">
          <h2 class="text-h5 text-sm-h4 font-weight-bold mb-4 text-white">{{ t("landing.ctaTitle") }}</h2>
          <p class="text-body-1 mb-6 mb-sm-8 mx-auto text-white" style="max-width: 560px; opacity: 0.92; line-height: 1.7;">{{ t("landing.ctaSubtitle") }}</p>
          <div class="d-flex justify-center ga-3 ga-sm-4 flex-wrap">
            <v-btn size="large" color="white" variant="flat" to="/login" prepend-icon="mdi-login" rounded="lg" class="px-6 px-sm-8 text-primary">{{ t("landing.ctaTry") }}</v-btn>
            <v-btn size="large" variant="outlined" color="white" href="https://github.com/2RL-AI/PulseID" target="_blank" prepend-icon="mdi-github" rounded="lg" class="px-6 px-sm-8">{{ t("landing.ctaStar") }}</v-btn>
          </div>
        </v-card>
      </v-container>
    </section>

    <!-- Footer -->
    <v-footer class="py-6 py-sm-8 d-flex flex-column" style="background: #0a0915; border-top: 1px solid rgba(99, 102, 241, 0.1);">
      <v-container>
        <v-row align="start">
          <v-col cols="12" md="4" class="mb-4 mb-md-0">
            <div class="d-flex align-center mb-3">
              <v-icon icon="mdi-pulse" size="24" color="primary" class="mr-2" />
              <span class="text-body-1 font-weight-bold gradient-text">PulseID</span>
            </div>
            <p class="text-caption text-medium-emphasis" style="line-height: 1.6;">{{ t("landing.footerDesc") }}</p>
          </v-col>
          <v-col cols="12" sm="6" md="4" class="mb-4 mb-md-0">
            <div class="text-caption font-weight-bold text-medium-emphasis mb-2" style="letter-spacing: 0.05em;">{{ t("landing.footerDevelopedBy") }}</div>
            <div class="d-flex align-center mb-2">
              <a href="https://2rl.ai" target="_blank" class="d-inline-flex align-center text-decoration-none">
                <img src="https://2rl.ai/images/logo-w_hu9295288637887756095.webp" alt="2RL.AI" style="height: 20px;" class="mr-2" />
              </a>
            </div>
            <div class="text-caption text-medium-emphasis" style="line-height: 1.7;">
              2RL S.&agrave; r.l.<br />
              16B Robert Schuman Strooss<br />
              L-5751 Frisange, Luxembourg<br />
              RCS Luxembourg: B301922<br />
              VAT: LU37044628
            </div>
          </v-col>
          <v-col cols="12" sm="6" md="4">
            <div class="text-caption font-weight-bold text-medium-emphasis mb-2" style="letter-spacing: 0.05em;">{{ t("landing.footerLinks") }}</div>
            <div class="d-flex flex-column ga-1">
              <a href="https://github.com/2RL-AI/PulseID" target="_blank" class="text-caption text-medium-emphasis text-decoration-none d-flex align-center">
                <v-icon icon="mdi-github" size="16" class="mr-2" /> {{ t("landing.footerGithub") }}
              </a>
              <a href="https://2rl.ai" target="_blank" class="text-caption text-medium-emphasis text-decoration-none d-flex align-center">
                <v-icon icon="mdi-web" size="16" class="mr-2" /> 2rl.ai
              </a>
              <a href="mailto:contact@2rl.ai" class="text-caption text-medium-emphasis text-decoration-none d-flex align-center">
                <v-icon icon="mdi-email-outline" size="16" class="mr-2" /> contact@2rl.ai
              </a>
            </div>
          </v-col>
        </v-row>
        <v-divider class="my-4 border-opacity-10" />
        <div class="text-caption text-medium-emphasis text-center">
          &copy; {{ new Date().getFullYear() }} {{ t("landing.footerCopyright") }}
        </div>
      </v-container>
    </v-footer>
  </div>
</template>

<script setup>
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const features = [
  { icon: "mdi-account-group-outline", titleKey: "landing.feat1Title", descKey: "landing.feat1Desc", color: "primary" },
  { icon: "mdi-card-account-details-outline", titleKey: "landing.feat2Title", descKey: "landing.feat2Desc", color: "info" },
  { icon: "mdi-clock-check-outline", titleKey: "landing.feat3Title", descKey: "landing.feat3Desc", color: "success" },
  { icon: "mdi-file-chart-outline", titleKey: "landing.feat4Title", descKey: "landing.feat4Desc", color: "warning" },
];

const steps = [
  { titleKey: "landing.step1Title", descKey: "landing.step1Desc" },
  { titleKey: "landing.step2Title", descKey: "landing.step2Desc" },
  { titleKey: "landing.step3Title", descKey: "landing.step3Desc" },
  { titleKey: "landing.step4Title", descKey: "landing.step4Desc" },
];
</script>

<style scoped>
.landing { background: #0f0e17; }
.section-padding { padding-top: 4rem; padding-bottom: 4rem; }
@media (min-width: 600px) { .section-padding { padding-top: 5rem; padding-bottom: 5rem; } }
@media (min-width: 960px) { .section-padding { padding-top: 6rem; padding-bottom: 6rem; } }
.gradient-text { background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-title { color: #e8e6f0; }
.hero-content { padding-left: 16px; padding-right: 16px; }
.hero-btn { min-width: 160px; }
@media (max-width: 599px) { .hero-btn { width: 100%; } }
.pulse-bg { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100%; max-width: 700px; aspect-ratio: 1; }
.pulse-ring { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); border-radius: 50%; border: 1px solid rgba(99, 102, 241, 0.12); animation: pulseExpand 4.5s ease-out infinite; }
.pulse-ring-1 { width: 35%; height: 35%; animation-delay: 0s; }
.pulse-ring-2 { width: 60%; height: 60%; animation-delay: 1.5s; }
.pulse-ring-3 { width: 85%; height: 85%; animation-delay: 3s; }
@keyframes pulseExpand { 0% { opacity: 0.5; transform: translate(-50%, -50%) scale(0.85); } 100% { opacity: 0; transform: translate(-50%, -50%) scale(1.4); } }
.scroll-indicator { position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); }
.bounce { animation: bounce 2s infinite; }
@keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-8px); } 60% { transform: translateY(-4px); } }
.feature-card { transition: transform 0.25s ease, border-color 0.25s ease; border-color: rgba(99, 102, 241, 0.12) !important; }
.feature-card:hover { transform: translateY(-6px); border-color: rgba(99, 102, 241, 0.4) !important; }
.compliance-card { background: rgba(99, 102, 241, 0.06) !important; border: 1px solid rgba(99, 102, 241, 0.15); }
.pricing-card { border-color: rgba(99, 102, 241, 0.25) !important; background: rgba(99, 102, 241, 0.04) !important; }
.cta-card { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important; }
.stats-row > div { min-width: 70px; }
</style>
