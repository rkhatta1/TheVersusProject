import { useState, useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2 } from 'lucide-react';
import { useAuth } from '@/AuthContext';
import { useToast } from "@/hooks/use-toast";

function SavedCaptions() {
  const [savedNews, setSavedNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { token } = useAuth();
  const { toast } = useToast();
  const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : {};

  const fetchSavedNews = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/captions', {
        headers: authHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSavedNews(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) { // Only fetch if authenticated
      fetchSavedNews();
    }
  }, [token]); // Re-fetch when token changes

  const handleDelete = async (captionId) => {
    try {
      const response = await fetch(`/api/captions/${captionId}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (!response.ok) {
        throw new Error(`Failed to delete caption.`);
      }
      // Remove the deleted item from the view
      setSavedNews(prevNews => prevNews.filter(item => item.id !== captionId));
      toast({ title: "Caption deleted!", description: "The news item has been removed from your saved list." });
    } catch (e) {
      toast({ title: "Error deleting caption", description: e.message, variant: "destructive" });
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Saved Captions</h1>
      {loading && <p className="text-center">Loading...</p>}
      {error && <p className="text-red-500 text-center">Error: {error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {savedNews.map((item) => (
          <Card key={item.id} className="bg-gray-800 border-gray-700 text-white flex flex-col justify-between">
            <div>
              <CardHeader>
                <CardTitle>{item.headline}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-400 mb-4">{item.summary}</p>
                <p className="text-xs text-gray-500 italic mb-4 truncate">Source: {item.source_caption}</p>
                <div className="border-t border-gray-700 pt-4">
                  <p className="text-md font-semibold text-teal-400">Versus Caption:</p>
                  <p className="text-gray-300">{item.versus_caption}</p>
                </div>
              </CardContent>
            </div>
            <CardFooter className="flex justify-between items-center">
              <p className="text-xs text-gray-500">Saved: {new Date(item.saved_at).toLocaleString()}</p>
              <Button variant="destructive" size="icon" onClick={() => handleDelete(item.id)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default SavedCaptions;
