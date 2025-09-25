export interface Draft {
  id: number
  title: string
  slug: string
  body_md?: string
  body_html?: string
  summary?: string
  tags: string[]
  hero_image_url?: string
  source?: string
  source_ref?: string
  created_at: string
  updated_at: string
  author?: string
  status: 'draft' | 'review' | 'approved' | 'published' | 'archived'
  scores?: Record<string, any>
  meta?: Record<string, any>
}
