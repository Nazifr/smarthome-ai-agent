export const ROOMS = {
  living: {
    id: 'living',
    name: 'Living Room',
    x: 40, y: 40, w: 320, h: 220,
    label: { x: 60, y: 70 },
    sensors: { x: 60, y: 220 },
    icon: { x: 320, y: 50 },
    motion: { x: 200, y: 150 },
    furniture: [
      { type: 'rect', x: 70, y: 200, w: 180, h: 38, r: 6 },
      { type: 'rect', x: 120, y: 150, w: 80, h: 28, r: 4 },
      { type: 'rect', x: 145, y: 56, w: 90, h: 8, r: 2 },
      { type: 'rect', x: 295, y: 60, w: 14, h: 180, r: 2 },
    ],
  },
  kitchen: {
    id: 'kitchen',
    name: 'Kitchen',
    x: 360, y: 40, w: 200, h: 160,
    label: { x: 380, y: 70 },
    sensors: { x: 380, y: 160 },
    icon: { x: 524, y: 50 },
    motion: { x: 460, y: 130 },
    furniture: [
      { type: 'rect', x: 370, y: 50, w: 180, h: 24, r: 3 },
      { type: 'rect', x: 526, y: 50, w: 24, h: 140, r: 3 },
      { type: 'rect', x: 390, y: 120, w: 110, h: 30, r: 4 },
    ],
  },
  bedroom: {
    id: 'bedroom',
    name: 'Bedroom',
    x: 560, y: 40, w: 200, h: 220,
    label: { x: 580, y: 70 },
    sensors: { x: 580, y: 220 },
    icon: { x: 724, y: 50 },
    motion: { x: 660, y: 150 },
    furniture: [
      { type: 'rect', x: 600, y: 100, w: 120, h: 90, r: 6 },
      { type: 'rect', x: 608, y: 108, w: 50, h: 14, r: 3 },
      { type: 'rect', x: 666, y: 108, w: 50, h: 14, r: 3 },
      { type: 'rect', x: 580, y: 110, w: 18, h: 28, r: 2 },
      { type: 'rect', x: 722, y: 110, w: 18, h: 28, r: 2 },
    ],
  },
  bathroom: {
    id: 'bathroom',
    name: 'Bathroom',
    x: 360, y: 200, w: 130, h: 180,
    label: { x: 376, y: 230 },
    sensors: { x: 376, y: 350 },
    icon: { x: 458, y: 210 },
    motion: { x: 425, y: 290 },
    furniture: [
      { type: 'rect', x: 380, y: 290, w: 90, h: 50, r: 8 },
      { type: 'rect', x: 380, y: 235, w: 40, h: 22, r: 3 },
      { type: 'circle', cx: 450, cy: 250, r: 12 },
    ],
  },
  hallway: {
    id: 'hallway',
    name: 'Hallway',
    x: 40, y: 260, w: 320, h: 80,
    label: { x: 60, y: 290 },
    sensors: { x: 60, y: 320 },
    icon: { x: 320, y: 270 },
    motion: { x: 200, y: 300 },
    furniture: [
      { type: 'rect', x: 60, y: 290, w: 280, h: 18, r: 2 },
    ],
  },
  office: {
    id: 'office',
    name: 'Office',
    x: 490, y: 260, w: 270, h: 120,
    label: { x: 510, y: 290 },
    sensors: { x: 510, y: 350 },
    icon: { x: 724, y: 270 },
    motion: { x: 620, y: 320 },
    furniture: [
      { type: 'rect', x: 510, y: 300, w: 160, h: 28, r: 3 },
      { type: 'circle', cx: 590, cy: 348, r: 14 },
    ],
  },
}

export function sparkPath(values, w = 100, h = 28, pad = 2) {
  if (!values || values.length === 0) return ''
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const step = (w - pad * 2) / (values.length - 1 || 1)
  return values.map((v, i) => {
    const x = pad + i * step
    const y = pad + (h - pad * 2) * (1 - (v - min) / range)
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
  }).join(' ')
}

export function sparkArea(values, w = 100, h = 28, pad = 2) {
  const line = sparkPath(values, w, h, pad)
  if (!line) return ''
  const last = pad + (values.length - 1) * ((w - pad * 2) / (values.length - 1 || 1))
  return `${line} L${last.toFixed(2)},${h - pad} L${pad},${h - pad} Z`
}
