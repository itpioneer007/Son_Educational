<script setup>
import { computed } from "vue";
import deepseekLogo from "../assets/ai/deepseek.svg";
import qwenLogo from "../assets/ai/qwen.svg";
import iflytekLogo from "../assets/ai/iflytek.svg";

/**
 * AI 品牌徽标：直接使用各家官方 logo（本地 SVG 资源，离线可用），
 * 配以名称文本，标明当前功能由哪个 AI 驱动。
 * name: deepseek | spark(讯飞星火) | zhiwen(讯飞智文) | qwen(通义千问)
 */
const props = defineProps({
  name: { type: String, required: true },
  size: { type: String, default: "md" }, // md | sm
  showLabel: { type: Boolean, default: true },
});

// 图标来源：Iconify 收录的官方品牌 SVG（logos:deepseek-icon / logos:qwen-icon /
// thesvg-color:iflytekcloud），已下载到 src/assets/ai/ 供离线使用。
// 讯飞星火与讯飞智文同属讯飞品牌，共用讯飞官方标识。
const BRANDS = {
  deepseek: { label: "DeepSeek", logo: deepseekLogo },
  spark: { label: "讯飞星火", logo: iflytekLogo },
  zhiwen: { label: "讯飞智文", logo: iflytekLogo },
  qwen: { label: "通义千问", logo: qwenLogo },
};

const brand = computed(
  () => BRANDS[props.name] || { label: props.name, logo: qwenLogo },
);
</script>

<template>
  <span class="aib" :class="`aib--${size}`">
    <span class="aib__mark">
      <img class="aib__logo" :src="brand.logo" :alt="`${brand.label} 标识`" />
    </span>
    <span v-if="showLabel" class="aib__label">{{ brand.label }}</span>
  </span>
</template>

<style scoped>
.aib {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.aib__mark {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
}

.aib__logo {
  width: 74%;
  height: 74%;
  object-fit: contain;
}

.aib--md .aib__mark {
  width: 24px;
  height: 24px;
}

.aib--sm .aib__mark {
  width: 18px;
  height: 18px;
  border-radius: 5px;
}

.aib__label {
  font-weight: 600;
  color: var(--ink-soft);
}

.aib--md .aib__label {
  font-size: 0.78rem;
}

.aib--sm .aib__label {
  font-size: 0.72rem;
}
</style>
