import { FileText, Search } from "lucide-react";
import { DocumentRecord } from "./types";

interface DocumentsSectionProps {
  documents: DocumentRecord[];
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  previewDocument: (doc: DocumentRecord) => void;
}

export function DocumentsSection({
  documents,
  searchQuery,
  setSearchQuery,
  previewDocument,
}: DocumentsSectionProps) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Document Intelligence & Corporate Policies</h2>
          <p className="text-xs text-muted-foreground">
            Search and review financial governance policies, close procedures, and customer invoices.
          </p>
        </div>
        <div className="relative min-w-[260px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents and policies..."
            className="w-full rounded-xl border border-border bg-[#0a2033] py-2 pl-9 pr-4 text-xs text-white placeholder-muted-foreground outline-none focus:border-primary"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {documents.map((doc) => (
          <div
            key={doc.id}
            onClick={() => previewDocument(doc)}
            className="cursor-pointer space-y-3 rounded-2xl border border-border bg-[#0a2033] p-5 transition hover:border-primary/50 hover:bg-[#0c2439]"
          >
            <div className="flex items-center justify-between">
              <FileText className="h-6 w-6 text-primary" />
              <span className="rounded-full border border-border bg-[#071a2b] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                {doc.document_type}
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-white">{doc.filename}</h3>
              <p className="mt-1 truncate font-mono text-[11px] text-muted-foreground">{doc.file_path}</p>
            </div>
            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Status: {doc.status}</span>
              <span className="text-primary hover:underline">View content →</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
