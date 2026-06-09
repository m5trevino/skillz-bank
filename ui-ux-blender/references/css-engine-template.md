# [Project Name] - Master CSS Engine

<!-- 1. FONT IMPORTS -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=[FONT_NAME]:wght@400;700&display=swap" rel="stylesheet">

<!-- 2. TAILWIND CONFIGURATION (For Runtime/Playground) -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          primary: "[HEX_CODE]",
          secondary: "[HEX_CODE]",
          accent: "[HEX_CODE]",
          surface: "[HEX_CODE]",
        },
        fontFamily: {
          custom: ["'[FONT_NAME]'", 'sans-serif'],
        },
      }
    }
  }
</script>

<!-- 3. CUSTOM UTILITY ENGINE -->
<style type="text/tailwindcss">
  @layer base {
    :root {
      --surface-shadow: [EXTRACTED_BOX_SHADOW];
      --recessed-shadow: [EXTRACTED_INSET_SHADOW];
      --accent-gradient: [EXTRACTED_LINEAR_GRADIENT];
    }
    body {
      @apply bg-surface text-white font-custom;
    }
  }

  @layer components {
    .surface-3d {
      @apply rounded-lg border border-white/10;
      box-shadow: var(--surface-shadow);
      background: var(--accent-gradient);
    }
    .recessed-panel {
      @apply rounded-lg bg-black/20;
      box-shadow: var(--recessed-shadow);
    }
    .metallic-text {
      @apply font-bold uppercase tracking-widest;
      background: var(--accent-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }
</style>
