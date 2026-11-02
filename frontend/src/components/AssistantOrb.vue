<template>
  <div class="orb-container" @click="$emit('click')">
    <div 
      class="iridescent-orb" 
      :class="{ 
        'is-processing': isProcessing, 
        'is-listening': isListening,
        'is-speaking': isSpeaking 
      }"
    >
      <div class="orb-specular"></div>
      <div class="orb-inner-wave"></div>
    </div>
    <div class="orb-reflection"></div>
    <div class="orb-status-caption">
      <span v-if="isListening" class="status-chip listening">
        <span class="mic-dot"></span> Escuchando voz...
      </span>
      <span v-else-if="isSpeaking" class="status-chip speaking">
        <span class="audio-waves"></span> Concierge hablando...
      </span>
      <span v-else-if="isProcessing" class="status-chip processing">
        <span class="spin-dot"></span> Procesando NLP...
      </span>
      <span v-else class="status-chip idle">
        ✨ Aura AI Concierge VIP
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isProcessing: {
    type: Boolean,
    default: false
  },
  isListening: {
    type: Boolean,
    default: false
  },
  isSpeaking: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style scoped>
.orb-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 0 8px;
  position: relative;
}

.iridescent-orb {
  position: relative;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: radial-gradient(
    circle at 35% 30%,
    #ffffff 0%,
    #bfe3ff 20%,
    #d1a9ff 45%,
    #f8b4d9 70%,
    #5f43b2 95%
  );
  box-shadow: 
    0 0 25px rgba(191, 227, 255, 0.7),
    0 0 50px rgba(209, 169, 255, 0.5),
    0 0 75px rgba(248, 180, 217, 0.35),
    inset 0 0 18px rgba(255, 255, 255, 0.9),
    inset -6px -6px 20px rgba(65, 34, 133, 0.55);
  cursor: pointer;
  animation: orbFloat 5s ease-in-out infinite, orbGlow 3.5s ease-in-out infinite alternate;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  overflow: hidden;
}

.orb-specular {
  position: absolute;
  top: 14%;
  left: 22%;
  width: 26px;
  height: 16px;
  background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0) 75%);
  border-radius: 50%;
  transform: rotate(-30deg);
  pointer-events: none;
}

.orb-inner-wave {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(
    from 180deg at 50% 50%,
    rgba(255, 255, 255, 0) 0deg,
    rgba(191, 227, 255, 0.4) 120deg,
    rgba(248, 180, 217, 0.5) 240deg,
    rgba(255, 255, 255, 0) 360deg
  );
  animation: rotateWave 8s linear infinite;
  mix-blend-mode: overlay;
}

.orb-reflection {
  width: 60px;
  height: 10px;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(162, 130, 220, 0.25) 0%, transparent 75%);
  filter: blur(4px);
  margin-top: 6px;
}

.orb-status-caption {
  margin-top: 8px;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.74rem;
  letter-spacing: 0.04em;
  padding: 3px 12px;
  border-radius: 999px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.status-chip.idle {
  color: #6a6155;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(210, 195, 175, 0.35);
}

.status-chip.listening {
  color: #c53030;
  background: #fde8e8;
  border: 1px solid #f8b4b4;
  font-weight: 600;
}

.status-chip.speaking {
  color: #2b6cb0;
  background: #ebf8ff;
  border: 1px solid #bee3f8;
  font-weight: 600;
}

.status-chip.processing {
  color: #744210;
  background: #fefcbf;
  border: 1px solid #faf089;
  font-weight: 600;
}

.mic-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #e53e3e;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

@keyframes orbFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-7px); }
}

@keyframes orbGlow {
  0% {
    box-shadow: 
      0 0 20px rgba(191, 227, 255, 0.6),
      0 0 40px rgba(209, 169, 255, 0.4);
  }
  100% {
    box-shadow: 
      0 0 35px rgba(191, 227, 255, 0.85),
      0 0 65px rgba(209, 169, 255, 0.65),
      0 0 90px rgba(248, 180, 217, 0.45);
  }
}

@keyframes rotateWave {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.is-listening {
  animation: listeningPulse 0.9s infinite alternate !important;
}

@keyframes listeningPulse {
  0% { transform: scale(1); filter: brightness(1); }
  100% { transform: scale(1.12); filter: brightness(1.3) hue-rotate(25deg); }
}

.is-processing {
  animation: processingPulse 1.1s infinite alternate !important;
}

@keyframes processingPulse {
  0% { transform: scale(0.96); filter: brightness(1); }
  100% { transform: scale(1.08); filter: brightness(1.25) drop-shadow(0 0 30px rgba(168, 85, 247, 0.9)); }
}
</style>

