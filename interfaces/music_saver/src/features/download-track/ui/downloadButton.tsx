import { Button } from "~/components/ui/button";
import { API_URL } from "~/shared/api/client";

interface DownloadButtonProps {
  contentId: number;
}
const DownloadButton = (props: DownloadButtonProps) => {
  return (
    <Button as="a" href={`${API_URL}tracks/${props.contentId}/download`} download="">
      Download
    </Button>
  );
};

export default DownloadButton;
