import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Play, Save, Trash2, StopCircle } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from '@/AuthContext';

function App() {
  const { token } = useAuth();

  const [news, setNews] = useState(() => {
    // Use a key that depends on the token (or user ID if available) for user-specific storage
    const userSpecificStorageKey = token ? `news_${token}` : 'news_guest';
    const savedNews = sessionStorage.getItem(userSpecificStorageKey);
    return savedNews ? JSON.parse(savedNews) : [];
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [url, setUrl] = useState('');
  const [urlLoading, setUrlLoading] = useState(false);
  const [urlError, setUrlError] = useState(null);
  const [timeLimit, setTimeLimit] = useState('24'); // Default to 24 hours

  const { toast } = useToast();

  const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : {};

  useEffect(() => {
    // Update sessionStorage with a user-specific key whenever news changes
    const userSpecificStorageKey = token ? `news_${token}` : 'news_guest';
    sessionStorage.setItem(userSpecificStorageKey, JSON.stringify(news));
  }, [news, token]); // Depend on news and token

  // Effect to re-initialize news when token changes (user logs in/out)
  useEffect(() => {
    const userSpecificStorageKey = token ? `news_${token}` : 'news_guest';
    const savedNews = sessionStorage.getItem(userSpecificStorageKey);
    setNews(savedNews ? JSON.parse(savedNews) : []);
  }, [token]);

  const fetchNews = async () => {
    setLoading(true);
    setError(null);
    // Do not clear news here, it will be handled by the useEffect on token change

    console.log("Fetching news...");
    console.log("Token:", token);
    console.log("Auth Headers:", authHeaders);

    try {
      const response = await fetch(`/api/breaking-news?time_limit=${timeLimit}`, {
        headers: authHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.message && data.message.includes("halted")) {
        toast({ title: "Process Halted", description: data.message, variant: "default" });
      } else {
        setNews(data.posts || []);
      }
    } catch (e) {
      setError(e.message);
      toast({ title: "Error fetching news", description: e.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    setUrlLoading(true);
    setUrlError(null);

    console.log("Submitting URL...");
    console.log("Token:", token);
    console.log("Auth Headers:", authHeaders);

    try {
      const response = await fetch('/api/process-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify({ url }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP error! status: ${response.status}`);
      }

      if (result.message === "This article has already been processed.") {
        setUrlError("This article has already been processed.");
        toast({ title: "Already Processed", description: "This article has already been processed.", variant: "default" });
      } else {
        setNews(prevNews => [result, ...prevNews]);
        setUrl('');
        toast({ title: "URL Processed", description: "The article from the URL has been processed." });
      }

    } catch (e) {
      setUrlError(e.message);
      toast({ title: "Error processing URL", description: e.message, variant: "destructive" });
    } finally {
      setUrlLoading(false);
    }
  };

  const handleSave = async (itemToSave) => {
    console.log("Saving item...");
    console.log("Token:", token);
    console.log("Auth Headers:", authHeaders);
    try {
      const response = await fetch('/api/captions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify(itemToSave),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to save caption.`);
      }
      // Mark the item as saved
      setNews(prevNews => prevNews.map(item => 
        item.headline === itemToSave.headline ? { ...item, saved: true } : item
      ));
      toast({ title: "Caption saved!", description: "The news item has been added to your saved list." });
    } catch (e) {
      toast({ title: "Error saving caption", description: e.message, variant: "destructive" });
    }
  };

  const handleTrash = (itemToTrash) => {
    // Just remove the item from the view
    setNews(prevNews => prevNews.filter(item => item.headline !== itemToTrash.headline));
    toast({ title: "Caption trashed", description: "The news item has been removed from the current view." });
  };

  const handleHalt = async () => {
    console.log("Sending halt signal...");
    console.log("Token:", token);
    console.log("Auth Headers:", authHeaders);
    try {
      const response = await fetch('/api/halt-loop', {
        method: 'POST',
        headers: authHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      toast({ title: "Halt Signal Sent", description: data.message });
    } catch (e) {
      toast({ title: "Error sending halt signal", description: e.message, variant: "destructive" });
    }
  };

  const renderSkeletons = () => {
    return Array.from({ length: 6 }).map((_, index) => (
      <Card key={index} className="bg-gray-800 border-gray-700 text-white">
        <div className='flex flex-col h-full justify-between'>
          <div className='flex flex-col'>
            <CardHeader>
              <Skeleton className="h-6 w-3/4 mb-2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-5/6 mb-4" />
              <Skeleton className="h-3 w-1/2" />
              <div className="border-t border-gray-700 pt-4">
                <Skeleton className="h-4 w-1/3 mb-2" />
                <Skeleton className="h-4 w-full" />
              </div>
            </CardContent>
          </div>
          <CardFooter className="flex justify-end space-x-2">
            <Skeleton className="h-8 w-8 rounded-md" />
            <Skeleton className="h-8 w-8 rounded-md" />
          </CardFooter>
        </div>
      </Card>
    ));
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">The Versus Project</h1>
      <div className="flex space-x-8 mb-8">
        <Button onClick={fetchNews} disabled={loading} className="flex w-[30%] space-x-[0.5rem] font-bold h-auto items-center">
          <Play className="h-4 w-4" />
          <div>{loading ? 'Running...' : 'Run the Main Loop'}</div>
        </Button>
        {loading && (
          <Button onClick={handleHalt} variant="destructive" className="flex space-x-[0.5rem] font-bold h-auto items-center">
            <StopCircle className="h-4 w-4" />
            <div>Halt Process</div>
          </Button>
        )}
        <div className=' flex items-center text-xl'>//</div>
        <form onSubmit={handleUrlSubmit} className="flex items-center space-x-2 flex-grow bg-gray-800 p-2 rounded-md">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste an article URL to process..."
            className="bg-gray-800 text-white w-full p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            required
          />
          <Button type="submit" disabled={urlLoading}>
            {urlLoading ? 'Processing...' : 'Process URL'}
          </Button>
        </form>
      </div>

      <div className="mb-8">
        <label htmlFor="time-limit" className="block text-sm font-medium text-gray-400 mb-2">Process news from the last:</label>
        <Select value={timeLimit} onValueChange={setTimeLimit}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select a time limit" />
          </SelectTrigger>
          <SelectContent>
            {[1, 3, 6, 9, 12, 15, 18, 21, 24].map(hour => (
              <SelectItem key={hour} value={String(hour)}>{hour} Hours</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {error && <p className="text-red-500 text-center">Error: {error}</p>}
      {urlError && <p className="text-red-500 text-center mt-2">{urlError}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? renderSkeletons() : news.map((item, index) => (
          <Card key={index} className="bg-gray-800 border-gray-700 text-white">
            <div className='flex flex-col h-full justify-between'>
            <div className='flex flex-col'>
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
            <CardFooter className="flex justify-end space-x-2">
              <Button variant="outline" size="icon" onClick={() => handleSave(item)} disabled={item.saved} className="text-black bg-green-100 hover:bg-green-300 border-0">
                <Save className="h-4 w-4" />
              </Button>
              <Button variant="destructive" size="icon" onClick={() => handleTrash(item)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </CardFooter>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default App;