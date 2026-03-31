import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Play, Clock, ExternalLink, Image as ImageIcon } from "lucide-react";

interface Video {
  id: number;
  title: string;
  channel: string;
  duration: string;
  thumbnail: string;
  url: string;
}

interface VideoCardProps {
  video: Video;
  expanded?: boolean;
}

const VideoCard = ({ video, expanded = false }: VideoCardProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [imgError, setImgError] = useState(false);

  const handlePlay = () => {
    setIsPlaying(true);
  };

  const getYouTubeEmbedUrl = (url: string) => {
    const videoId = url.split('v=')[1]?.split('&')[0];
    return `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
  };

  const getYouTubeThumbnail = (url: string) => {
    const videoId = url.split('v=')[1]?.split('&')[0];
    return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
  };

  return (
    <Card className="shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group w-full">
      <CardContent className="p-0">
        {expanded ? (
          /* Expanded Layout - Full width video */
          <div className="flex flex-col">
            {/* Video Section */}
            <div className="relative aspect-video bg-black">
              {isPlaying ? (
                <iframe
                  src={getYouTubeEmbedUrl(video.url)}
                  className="w-full h-full"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  title={video.title}
                />
              ) : (
                <>
                  {imgError ? (
                    <div className="w-full h-full bg-gray-800 flex flex-col items-center justify-center text-gray-400">
                      <ImageIcon className="h-8 w-8 mb-2 opacity-50" />
                      <span className="text-xs font-medium">Thumbnail Unavailable</span>
                    </div>
                  ) : (
                    <img
                      src={getYouTubeThumbnail(video.url)}
                      alt={video.title}
                      className="w-full h-full object-cover"
                      onError={() => setImgError(true)}
                    />
                  )}
                  <div className="absolute inset-0 bg-black/30 flex items-center justify-center group-hover:bg-black/40 transition-colors">
                    <Button
                      size="lg"
                      onClick={handlePlay}
                      className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm"
                    >
                      <Play className="mr-2 h-4 w-4 sm:h-5 sm:w-5 fill-current" />
                      <span className="hidden xs:inline">Play</span>
                    </Button>
                  </div>
                  <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                    {video.duration}
                  </div>
                </>
              )}
            </div>
            
            {/* Info Section */}
            <div className="p-3 sm:p-4 lg:p-6">
              <h3 className="font-semibold text-gray-900 mb-2 text-base sm:text-lg lg:text-xl">
                {video.title}
              </h3>
              
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-sm sm:text-base text-gray-600">{video.channel}</p>
                  <div className="flex items-center text-xs sm:text-sm text-gray-500">
                    <Clock className="mr-1 h-3 w-3 sm:h-4 sm:w-4" />
                    {video.duration}
                  </div>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(video.url, '_blank')}
                  className="hover:bg-blue-600 hover:text-white w-full sm:w-auto"
                >
                  <ExternalLink className="mr-1 h-3 w-3 sm:h-4 sm:w-4" />
                  <span className="sm:hidden">Open in YouTube</span>
                  <span className="hidden sm:inline">YouTube</span>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* Compact Layout - Side by side on larger screens, stacked on mobile */
          <div className="flex flex-col xs:flex-row">
            {/* Video Thumbnail */}
            <div className="relative w-full xs:w-32 sm:w-40 md:w-48 flex-shrink-0 bg-black">
              <div className="aspect-video xs:aspect-square xs:h-24 sm:h-32 md:h-36">
                {isPlaying ? (
                  <iframe
                    src={getYouTubeEmbedUrl(video.url)}
                    className="w-full h-full"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    title={video.title}
                  />
                ) : (
                  <>
                    {imgError ? (
                      <div className="w-full h-full bg-gray-800 flex flex-col items-center justify-center text-gray-400">
                        <ImageIcon className="h-6 w-6 sm:h-8 sm:w-8 mb-1 opacity-50" />
                      </div>
                    ) : (
                      <img
                        src={getYouTubeThumbnail(video.url)}
                        alt={video.title}
                        className="w-full h-full object-cover"
                        onError={() => setImgError(true)}
                      />
                    )}
                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center group-hover:bg-black/40 transition-colors">
                      <Button
                        size="sm"
                        onClick={handlePlay}
                        className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm text-xs sm:text-sm"
                      >
                        <Play className="mr-1 h-3 w-3 sm:h-4 sm:w-4 fill-current" />
                        <span className="hidden sm:inline">Play</span>
                      </Button>
                    </div>
                    <div className="absolute bottom-1 right-1 sm:bottom-2 sm:right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 sm:px-2 sm:py-1 rounded">
                      {video.duration}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Video Info */}
            <div className="p-3 sm:p-4 flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base line-clamp-2 sm:line-clamp-3">
                {video.title}
              </h3>
              
              <div className="flex flex-col xs:flex-row xs:items-start xs:justify-between gap-2">
                <div className="space-y-1 min-w-0 flex-1">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">{video.channel}</p>
                  <div className="flex items-center text-xs text-gray-500">
                    <Clock className="mr-1 h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{video.duration}</span>
                  </div>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(video.url, '_blank')}
                  className="text-gray-400 hover:text-gray-600 p-1 xs:p-2 self-start xs:self-center"
                >
                  <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span className="sr-only">Open in YouTube</span>
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default VideoCard;