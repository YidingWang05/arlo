// Original illustration assets and explicit, non-medical fixture data. No real family or purchase history.
export const demoPhotos = [{
  id: 'demo-landscape', image_url: '/demo-assets/landscape.svg',
  caption: 'A quiet moment by the water · Demo illustration', timestamp: '2026-10-31',
}];

export const demoVision = {
  category: 'OTHER', headline_large: 'Keep this label for reference',
  audio_script: 'This is a demonstration, not a reading of your photo. Keep the original label and check unclear medicine instructions with a pharmacist.',
  action_items: ['Keep the original label', 'Ask a pharmacist about unclear instructions'], is_blurry: false,
};

export const demoMemory = {
  spoken_prompt: 'Which bottle looks familiar?',
  candidates: [
    { item_id: 'demo-blue', name: 'Blue household cleaner', image_url: '/demo-assets/bottle-blue.svg', display_tag: 'Example A · Blue bottle' },
    { item_id: 'demo-amber', name: 'Amber hand wash', image_url: '/demo-assets/bottle-amber.svg', display_tag: 'Example B · Amber bottle' },
  ],
};
