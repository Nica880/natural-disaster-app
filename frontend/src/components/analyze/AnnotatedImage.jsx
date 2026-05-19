/** Shows the YOLO-annotated image (boxes / masks rendered server-side).
 *  Renders nothing if the source is missing. */
export default function AnnotatedImage({ src, alt = 'Annotated' }) {
  if (!src) return null
  return (
    <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-100 mb-4">
      <img src={src} alt={alt} className="w-full max-h-[420px] object-contain bg-slate-900/5" />
    </div>
  )
}
