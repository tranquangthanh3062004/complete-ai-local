-- Kích hoạt pgvector extension
create extension if not exists vector;

-- Xóa bảng cũ nếu có (cẩn thận nếu bạn có dữ liệu khác)
-- drop table if exists documents;

-- Tạo bảng documents để lưu trữ văn bản và vector
create table documents (
  id bigserial primary key,
  content text, -- Nội dung văn bản
  metadata jsonb, -- Metadata (như tên file, chunk id)
  embedding vector(768) -- Google Gemini dùng vector 768 dimensions (models/gemini-embedding-2)
);

-- Tạo function tìm kiếm (match_documents)
create or replace function match_documents (
  query_embedding vector(768),
  match_count int default null,
  filter jsonb default '{}'
) returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    content,
    metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where metadata @> filter
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Cấp quyền truy cập cho role anon và authenticated
grant usage on schema public to anon, authenticated;
grant all privileges on table documents to anon, authenticated;
grant execute on function match_documents to anon, authenticated;
