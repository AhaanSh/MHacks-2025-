import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export const SearchBar = ({ onSearch }: SearchBarProps) => {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = () => {
    if (!query.trim()) return;
    
    setIsLoading(true);
    
    // Simulate search delay
    setTimeout(() => {
      setIsLoading(false);
      onSearch(query);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="w-full">
      {/* Prominent, central search bar per design.md */}
      <div className="bg-card rounded-2xl p-2 shadow-sm border border-border/50">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted w-6 h-6" />
            <Input
              placeholder="Describe your dream apartment..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="pl-12 h-14 text-lg border-0 bg-transparent search-focus text-heading placeholder:text-muted"
              disabled={isLoading}
            />
          </div>
          <Button 
            onClick={handleSearch}
            disabled={isLoading || !query.trim()}
            className="h-14 px-8 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-xl transition-all hover:shadow-md"
          >
            {isLoading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              "Search"
            )}
          </Button>
        </div>
      </div>
      
      {isLoading && (
        <div className="mt-6 text-center fade-in-up">
          <div className="inline-flex items-center gap-3 bg-card px-6 py-3 rounded-full shadow-sm">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <span className="text-body font-medium">Searching for perfect matches...</span>
          </div>
        </div>
      )}
    </div>
  );
};