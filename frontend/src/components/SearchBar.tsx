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
    <div className="w-full max-w-2xl mx-auto mb-8">
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
          <Input
            placeholder="Describe your dream apartment..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="pl-10 h-12 text-lg border-2 border-primary/20 focus:border-primary transition-colors"
            disabled={isLoading}
          />
        </div>
        <Button 
          onClick={handleSearch}
          disabled={isLoading || !query.trim()}
          className="h-12 px-6 bg-primary hover:bg-primary-hover text-primary-foreground font-semibold transition-all hover:scale-105"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            "Search"
          )}
        </Button>
      </div>
      
      {isLoading && (
        <div className="mt-4 text-center text-muted-foreground fade-in-up">
          <div className="inline-flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Searching for perfect matches...
          </div>
        </div>
      )}
    </div>
  );
};