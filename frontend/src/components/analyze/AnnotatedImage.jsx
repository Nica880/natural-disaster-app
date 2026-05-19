/** Shows either the YOLO-annotated image (boxes/masks drawn server-side)
 *  or the user's original upload, controlled by `showOverlay`.
 *  Renders nothing if neither source is available. */
export default function AnnotatedImage({ src, originalSrc, showOverlay = true, alt = 'Image' }) {
  const finalSrc = (showOverlay && src) ? src : (originalSrc || src)
  if (!finalSrc) return null
  return (
    <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-100 mb-4">
      <img
        src={finalSrc}
        alt={alt}
        className="w-full max-h-[420px] object-contain bg-slate-900/5 transition-opacity"
      />
    </div>
  )
}
